//! Training und Laden des Modells.

use crate::features::{class_to_char, fix_case, normalize, relative_heights};
use crate::model::{to_tensors, Net};
use crate::segment::segment;
use crate::synth::{generate, load_fonts, Rng, Sample};
use candle_core::{DType, Device, Tensor, D};
use candle_nn::ops::softmax;
use candle_nn::{loss, AdamW, Optimizer, ParamsAdamW, VarBuilder, VarMap};
use image::RgbImage;
use std::fmt::Display;
use std::path::Path;

const BATCH: usize = 64;

/// Wandelt beliebige Fehler in String um (für einheitliche Rückgabe).
fn s<E: Display>(e: E) -> String {
    e.to_string()
}

/// Trainiert das Netz auf künstlichen Zeichen und speichert es als .safetensors.
/// Gibt die Trainings-Genauigkeit der letzten Epoche zurück (0.0 - 1.0).
pub fn train(
    fonts_dir: &str,
    model_path: &str,
    rounds: usize,
    epochs: usize,
) -> Result<f32, String> {
    let fonts = load_fonts(Path::new(fonts_dir))?;
    println!("{} Fonts geladen, erzeuge Trainingsdaten ...", fonts.len());

    let mut rng = Rng::new(0x5EED_1234);
    let samples: Vec<Sample> = generate(&fonts, rounds, &mut rng);
    println!("{} Trainingszeichen erzeugt", samples.len());

    let dev = Device::Cpu;
    let varmap = VarMap::new();
    let vb = VarBuilder::from_varmap(&varmap, DType::F32, &dev);
    let net = Net::new(vb).map_err(s)?;
    let params = ParamsAdamW {
        lr: 1e-3,
        ..Default::default()
    };
    let mut opt = AdamW::new(varmap.all_vars(), params).map_err(s)?;

    let mut order: Vec<usize> = (0..samples.len()).collect();
    let mut accuracy = 0.0;

    for epoch in 1..=epochs {
        rng.shuffle(&mut order);
        let mut correct = 0usize;
        let mut loss_sum = 0f32;
        let mut batches = 0usize;

        for chunk in order.chunks(BATCH) {
            let batch: Vec<&Sample> = chunk.iter().map(|&i| &samples[i]).collect();
            let pixels: Vec<&[f32]> = batch.iter().map(|s| s.pixels.as_slice()).collect();
            let rel: Vec<f32> = batch.iter().map(|s| s.rel_height).collect();
            let labels: Vec<u32> = batch.iter().map(|s| s.label).collect();

            let (x, r) = to_tensors(&pixels, &rel, &dev).map_err(s)?;
            let y = Tensor::from_vec(labels.clone(), batch.len(), &dev).map_err(s)?;

            let logits = net.forward(&x, &r).map_err(s)?;
            let l = loss::cross_entropy(&logits, &y).map_err(s)?;
            opt.backward_step(&l).map_err(s)?;

            loss_sum += l.to_scalar::<f32>().map_err(s)?;
            batches += 1;
            let pred = logits
                .argmax(D::Minus1)
                .map_err(s)?
                .to_vec1::<u32>()
                .map_err(s)?;
            correct += pred.iter().zip(&labels).filter(|(p, t)| p == t).count();
        }

        accuracy = correct as f32 / samples.len() as f32;
        println!(
            "Epoche {}/{}: Loss {:.3}, Genauigkeit {:.1} %",
            epoch,
            epochs,
            loss_sum / batches as f32,
            accuracy * 100.0
        );
    }

    varmap.save(model_path).map_err(s)?;
    println!("Modell gespeichert: {}", model_path);
    Ok(accuracy)
}

/// Geladenes Modell, bereit zum Lesen von Captchas.
pub struct Ocr {
    net: Net,
    dev: Device,
}

impl Ocr {
    pub fn load(model_path: &str) -> Result<Self, String> {
        let dev = Device::Cpu;
        let mut varmap = VarMap::new();
        let vb = VarBuilder::from_varmap(&varmap, DType::F32, &dev);
        // Netz zuerst anlegen (erzeugt die Variablen), dann Gewichte reinladen
        let net = Net::new(vb).map_err(s)?;
        varmap.load(model_path).map_err(s)?;
        Ok(Self { net, dev })
    }

    /// Captcha-Bild -> die `count` wahrscheinlichsten Lesarten, beste zuerst.
    pub fn read_top(&self, img: &RgbImage, count: usize) -> Result<Vec<String>, String> {
        let masks = segment(img);
        if masks.is_empty() {
            return Ok(vec![String::new()]);
        }
        let rel = relative_heights(&masks);
        let normalized: Vec<Vec<f32>> = masks.iter().map(normalize).collect();
        let pixels: Vec<&[f32]> = normalized.iter().map(|v| v.as_slice()).collect();

        let (x, r) = to_tensors(&pixels, &rel, &self.dev).map_err(s)?;
        let logits = self.net.forward(&x, &r).map_err(s)?;
        // Wahrscheinlichkeiten: pro Zeichen-Position 62 Werte, Summe = 1
        let probs: Vec<Vec<f32>> = softmax(&logits, D::Minus1)
            .map_err(s)?
            .to_vec2::<f32>()
            .map_err(s)?;

        // Platz 1: an jeder Position das wahrscheinlichste Zeichen
        let best: Vec<u32> = probs.iter().map(|p| argmax(p)).collect();

        // Alle Einzel-Tausche (Position, anderes Zeichen), bewertet danach,
        // wie viel Wahrscheinlichkeit der Tausch kostet:
        // ratio = p(neues Zeichen) / p(bestes Zeichen), 1.0 = kostet nichts
        let mut swaps: Vec<(f32, usize, u32)> = Vec::new();
        for (pos, p) in probs.iter().enumerate() {
            let top = p[best[pos] as usize];
            for (class, &pc) in p.iter().enumerate() {
                if class as u32 != best[pos] {
                    swaps.push((pc / top, pos, class as u32));
                }
            }
        }
        swaps.sort_by(|a, b| b.0.total_cmp(&a.0));

        let to_text = |classes: &[u32]| -> String {
            classes
                .iter()
                .zip(&rel)
                .map(|(&c, &h)| fix_case(class_to_char(c), h))
                .collect()
        };

        let mut results = vec![to_text(&best)];
        for (_, pos, class) in swaps {
            if results.len() >= count {
                break;
            }
            let mut alt = best.clone();
            alt[pos] = class;
            let text = to_text(&alt);
            // z.B. z -> Z wird durch die Höhenregel wieder zu z: kein neuer Text
            if !results.contains(&text) {
                results.push(text);
            }
        }
        Ok(results)
    }
}

/// Index des größten Wertes
fn argmax(values: &[f32]) -> u32 {
    values
        .iter()
        .enumerate()
        .max_by(|a, b| a.1.total_cmp(b.1))
        .map(|(i, _)| i as u32)
        .unwrap_or(0)
}
