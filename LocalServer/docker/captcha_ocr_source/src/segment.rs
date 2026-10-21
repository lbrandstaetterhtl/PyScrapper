//! Zerlegt ein Captcha in einzelne Zeichen-Masken (schwarz/weiß).

use image::{GrayImage, Luma, RgbImage};
use imageproc::distance_transform::Norm;
use imageproc::morphology::open;
use imageproc::region_labelling::{connected_components, Connectivity};
use std::collections::HashMap;

/// Mindest-Sättigung (0-255), ab der ein Pixel als Zeichen-Pixel gilt.
const SAT_MIN: u32 = 40;
/// Fast schwarze Pixel (Rausch-Punkte) ignorieren.
const DARK_MIN: u8 = 40;
/// Anzahl Zeichen pro Captcha.
pub const CHARS_PER_CAPTCHA: usize = 5;

/// Bounding Box + Pixelanzahl einer zusammenhängenden Fläche.
#[derive(Clone, Copy)]
struct Blob {
    x0: u32,
    y0: u32,
    x1: u32,
    y1: u32,
    count: u32,
    label: u32,
}

fn is_character_pixel(r: u8, g: u8, b: u8) -> bool {
    let max_c = r.max(g).max(b);
    let min_c = r.min(g).min(b);
    if max_c <= DARK_MIN {
        return false;
    }
    let sat = (max_c - min_c) as u32 * 255 / max_c as u32;
    sat > SAT_MIN
}

/// Farbige Pixel = 255, Rest = 0.
fn binarize(img: &RgbImage) -> GrayImage {
    let mut bin = GrayImage::new(img.width(), img.height());
    for (x, y, p) in img.enumerate_pixels() {
        let v = if is_character_pixel(p[0], p[1], p[2]) {
            255
        } else {
            0
        };
        bin.put_pixel(x, y, Luma([v]));
    }
    bin
}

/// Sammelt für jedes Label (außer 0 = Hintergrund) Bounding Box und Pixelanzahl.
fn collect_blobs(labels: &image::ImageBuffer<Luma<u32>, Vec<u32>>) -> Vec<Blob> {
    let mut boxes: HashMap<u32, Blob> = HashMap::new();
    for (x, y, p) in labels.enumerate_pixels() {
        let label = p[0];
        if label == 0 {
            continue;
        }
        let b = boxes.entry(label).or_insert(Blob {
            x0: x,
            y0: y,
            x1: x,
            y1: y,
            count: 0,
            label,
        });
        b.x0 = b.x0.min(x);
        b.y0 = b.y0.min(y);
        b.x1 = b.x1.max(x);
        b.y1 = b.y1.max(y);
        b.count += 1;
    }
    boxes.into_values().collect()
}

/// Schneidet genau die Pixel eines Labels aus seiner Bounding Box aus.
fn crop_blob(labels: &image::ImageBuffer<Luma<u32>, Vec<u32>>, b: &Blob) -> GrayImage {
    let bw = b.x1 - b.x0 + 1;
    let bh = b.y1 - b.y0 + 1;
    let mut crop = GrayImage::new(bw, bh);
    for y in 0..bh {
        for x in 0..bw {
            let keep = labels.get_pixel(b.x0 + x, b.y0 + y)[0] == b.label;
            crop.put_pixel(x, y, Luma([if keep { 255 } else { 0 }]));
        }
    }
    crop
}

/// Captcha -> Zeichen-Masken, von links nach rechts sortiert.
/// Liefert höchstens CHARS_PER_CAPTCHA Einträge (weniger, wenn nicht genug gefunden).
pub fn segment(img: &RgbImage) -> Vec<GrayImage> {
    let bin = binarize(img);
    // Opening entfernt dünne Linien und Rauschen, übrig bleiben die Zeichen-Kerne
    let core = open(&bin, Norm::LInf, 1);
    let labels = connected_components(&core, Connectivity::Eight, Luma([0u8]));

    let mut blobs: Vec<Blob> = collect_blobs(&labels)
        .into_iter()
        .filter(|b| {
            let bw = b.x1 - b.x0 + 1;
            let bh = b.y1 - b.y0 + 1;
            if b.count < 30 || bw < 4 || bh < 8 {
                return false; // Rauschreste
            }
            let aspect = bw.max(bh) as f32 / bw.min(bh) as f32;
            if aspect > 6.0 {
                return false; // Linienstücke
            }
            let fill = b.count as f32 / (bw * bh) as f32;
            fill >= 0.20 // hohle Kreise raus
        })
        .collect();

    blobs.sort_by(|a, b| b.count.cmp(&a.count));
    blobs.truncate(CHARS_PER_CAPTCHA);
    blobs.sort_by_key(|b| b.x0);

    blobs.iter().map(|b| crop_blob(&labels, b)).collect()
}

/// Behält nur die größte zusammenhängende Fläche einer Maske und schneidet
/// auf ihre Bounding Box zu. Wird für die künstlichen Trainingszeichen benutzt,
/// damit sie genauso aussehen wie die Ausschnitte aus `segment`.
pub fn largest_component_crop(mask: &GrayImage) -> Option<GrayImage> {
    let labels = connected_components(mask, Connectivity::Eight, Luma([0u8]));
    let biggest = collect_blobs(&labels).into_iter().max_by_key(|b| b.count)?;
    Some(crop_blob(&labels, &biggest))
}
