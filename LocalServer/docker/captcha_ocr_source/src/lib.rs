extern crate core;

mod config;
mod cnn;
mod bbox;

use std::collections::HashMap;
use candle_core::{Device, Tensor};
use candle_nn::ops::softmax;
use image::{imageops, DynamicImage, GrayImage, ImageBuffer, Luma, Rgb, RgbImage};
use imageproc::filter::median_filter;
use imageproc::region_labelling::{connected_components, Connectivity};
use pyo3::exceptions::{PyValueError};
use pyo3::prelude::*;
use crate::bbox::BBox;
use crate::cnn::*;
use crate::config::*;

#[pymodule]
fn ocr(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(img_to_text, m)?)?;
    Ok(())
}

#[pyfunction]
fn img_to_text(image_path: &str, ocr_dir: &str) -> PyResult<Vec<String>> {
    let config = match Config::load(ocr_dir) {
        Ok(c) => c,
        Err(e) => return Err(PyValueError::new_err(e.to_string())),
    };

    let device = config.device().map_err(|e| PyValueError::new_err(e.to_string()))?;
    let tensors = load_and_split(image_path, &device).map_err(|e| PyValueError::new_err(e.to_string()))?;
    let cnn = CNN::load(&device, &config, ocr_dir).map_err(|e| PyValueError::new_err(e.to_string()))?;

    let mut per_position = Vec::new();
    for tensor in tensors {
        let logits = cnn.forward(&tensor).map_err(|e| PyValueError::new_err(e.to_string()))?;
        per_position.push(top_k(&logits, config.max_candidates, &cnn).map_err(|e| PyValueError::new_err(e.to_string()))?);
    }

    let ranked = candidates(&per_position, config.max_candidates);
    let results = ranked.into_iter().map(|(c, _)| c).collect::<Vec<String>>();
    Ok(results)
}

fn top_k(logits: &Tensor, k: usize, cnn: &CNN) -> Result<Vec<(char, f32)>, String> {
    let probs: Vec<f32> = softmax(&logits.squeeze(0).map_err(|e| e.to_string())?, candle_core::D::Minus1)
        .map_err(|e| e.to_string())?
        .to_vec1()
        .map_err(|e| e.to_string())?;

    if probs.len() != cnn.vocab.len() {
        return Err(format!(
            "Model returns {} classes, vocab has {} characters",
            probs.len(),
            cnn.vocab.len()
        ));
    }

    let mut ranked: Vec<(char, f32)> = probs
        .into_iter()
        .enumerate()
        .map(|(i, p)| (cnn.vocab.decode(i as u32), p))
        .collect();
    ranked.sort_by(|a, b| b.1.total_cmp(&a.1));
    ranked.truncate(k);
    Ok(ranked)
}
fn candidates(per_position: &[Vec<(char, f32)>], max: usize) -> Vec<(String, f32)> {
    let mut result: Vec<(String, f32)> = vec![(String::new(), 0.0)];

    for options in per_position {
        let mut next = Vec::with_capacity(result.len() * options.len());
        for (prefix, logp) in &result {
            for &(ch, p) in options {
                let mut s = prefix.clone();
                s.push(ch);
                next.push((s, logp + p.max(1e-9).ln()));
            }
        }
        next.sort_by(|a, b| b.1.total_cmp(&a.1));
        next.truncate(max);
        result = next;
    }

    result.into_iter().map(|(s, logp)| (s, logp.exp())).collect()
}

fn to_emnist(crop: &GrayImage) -> GrayImage {
    let (cw, ch) = crop.dimensions();
    let scale = 20.0 / cw.max(ch) as f32;
    let nw = ((cw as f32 * scale).round() as u32).clamp(1, 20);
    let nh = ((ch as f32 * scale).round() as u32).clamp(1, 20);
    let resized = imageops::resize(crop, nw, nh, imageops::FilterType::Triangle);

    let mut out = GrayImage::from_pixel(28, 28, Luma([0]));
    let dx = (28 - nw) / 2;
    let dy = (28 - nh) / 2;
    imageops::replace(&mut out, &resized, dx as i64, dy as i64);
    out
}

pub fn load_and_split(path: &str, device: &Device) -> Result<Vec<Tensor>, String> {
    let img = load_image(path.to_string()).map_err(|error| error.to_string())?;

    let letters = image_clean_and_split_up(img).map_err(|error| error.to_string())?;

    let mut tensors: Vec<Tensor> = Vec::new();
    for letter in letters {
        let pixel: Vec<f32> = letter.into_raw().iter()
            .map(|&p| p as f32 / 255.0).collect();

        let t = Tensor::from_vec(pixel, (1, 1, 28, 28), &device).map_err(|error| error.to_string())?;

        tensors.push(t);
    }

    Ok(tensors)
}

fn load_image(path: String) -> Result<DynamicImage, String> {
    let img = image::open(path)
        .map_err(|e| e.to_string())?;
    Ok(img)
}

fn image_clean_and_split_up(image: DynamicImage) -> Result<Vec<GrayImage>, String> {
    let gray = image.grayscale();
    let mut black_and_white = make_black_and_white(&gray.to_rgb8());
    black_and_white = median_filter(&black_and_white, 1, 1);

    let letters = image_split_up(black_and_white).map_err(|error| error.to_string())?;

    Ok(letters)
}

fn make_black_and_white(image: &RgbImage) -> GrayImage {
    let bg = background_color(&image);

    let max_dist = (3.0f32 * 255.0 * 255.0).sqrt();
    let (w, h) = image.dimensions();
    let mut black_and_white = GrayImage::new(w, h);
    for (x, y, px) in image.enumerate_pixels() {
        let Rgb([r, g, b]) = *px;
        let dr = r as f32 - bg[0];
        let dg = g as f32 - bg[1];
        let db = b as f32 - bg[2];
        let d = (dr * dr + dg * dg + db * db).sqrt() / max_dist * 255.0;
        black_and_white.put_pixel(x, y, Luma([if d > 32.0 { 255 } else { 0 }]));
    }

    black_and_white
}

fn background_color(img: &RgbImage) -> [f32; 3] {
    let mut ch: [Vec<u8>; 3] = [Vec::new(), Vec::new(), Vec::new()];
    for p in img.pixels() {
        for c in 0..3 {
            ch[c].push(p.0[c]);
        }
    }
    let mut bg = [0.0f32; 3];
    for c in 0..3 {
        ch[c].sort_unstable();
        bg[c] = ch[c][ch[c].len() / 2] as f32;
    }
    bg
}

fn image_split_up(image: GrayImage) -> Result<Vec<GrayImage>, String> {
    let labels = connected_components(&image.clone(), Connectivity::Eight, Luma([0]));

    let min_area = 30;
    let min_fill = 0.15;
    let mut bboxes: Vec<BBox> = get_bounding_boxes(&labels)
        .into_iter()
        .filter(|b| b.area >= min_area)
        .filter(|b| b.fill() >= min_fill)
        .collect();

    let max_h = bboxes.iter().map(|b| b.height()).max().unwrap_or(0);
    bboxes.retain(|b| b.height() * 10 >= max_h * 4);

    let mut result: Vec<GrayImage> = Vec::new();

    for bbox in bboxes {
        result.push(match crop_letter(&image.clone(), &bbox, 3).map(|c| to_emnist(&c)) {
            Some(result) => result,
            None => continue,
        });
    }

    Ok(result)
}

fn get_bounding_boxes(labels: &ImageBuffer<Luma<u32>, Vec<u32>>) -> Vec<BBox> {
    let mut boxes: HashMap<u32, BBox> = HashMap::new();

    for (x, y, px) in labels.enumerate_pixels() {
        let label = px.0[0];
        if label == 0 {
            continue;
        }

        boxes
            .entry(label)
            .and_modify(|b| {
                b.min_x = b.min_x.min(x);
                b.max_x = b.max_x.max(x);
                b.min_y = b.min_y.min(y);
                b.max_y = b.max_y.max(y);
                b.area += 1;
            })
            .or_insert(BBox { min_x: x, min_y: y, max_x: x, max_y: y, area: 1});
    }

    let mut result: Vec<BBox> = boxes.into_values().collect();
    result.sort_by_key(|b| b.min_x);
    result
}
fn crop_letter(src: &GrayImage, b: &BBox, pad: u32) -> Option<GrayImage> {
    let (w, h) = src.dimensions();

    let left = b.min_x.saturating_sub(pad);
    let top = b.min_y.saturating_sub(pad);
    let right = (b.max_x + 1 + pad).min(w);
    let bottom = (b.max_y + 1 + pad).min(h);

    if right <= left || bottom <= top {
        return None;
    }

    Some(imageops::crop_imm(src, left, top, right - left, bottom - top).to_image())
}