//! Erzeugt künstliche Trainingszeichen aus Schriftarten.
//! Jedes Zeichen wird gedreht, verschieden stark binarisiert und wie im
//! echten Ablauf "angefressen" (Opening), damit es den Captcha-Ausschnitten ähnelt.

use crate::features::{normalize, CHARS};
use crate::segment::largest_component_crop;
use ab_glyph::{FontVec, PxScale};
use image::{GrayImage, Luma};
use imageproc::distance_transform::Norm;
use imageproc::drawing::draw_text_mut;
use imageproc::geometric_transformations::{rotate_about_center, Border, Interpolation};
use imageproc::morphology::open;
use std::path::Path;

/// Kleiner Zufallsgenerator (xorshift), damit wir kein extra Crate brauchen.
pub struct Rng(u64);

impl Rng {
    pub fn new(seed: u64) -> Self {
        Rng(seed.max(1))
    }

    pub fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.0 = x;
        x
    }

    /// Ganzzahl im Bereich lo..=hi
    pub fn range(&mut self, lo: u32, hi: u32) -> u32 {
        lo + (self.next_u64() % (hi - lo + 1) as u64) as u32
    }

    /// Kommazahl im Bereich lo..hi
    pub fn float(&mut self, lo: f32, hi: f32) -> f32 {
        let unit = (self.next_u64() >> 40) as f32 / (1u64 << 24) as f32;
        lo + unit * (hi - lo)
    }

    /// true mit Wahrscheinlichkeit p
    pub fn chance(&mut self, p: f32) -> bool {
        self.float(0.0, 1.0) < p
    }

    /// Index im Bereich 0..n
    pub fn index(&mut self, n: usize) -> usize {
        (self.next_u64() % n as u64) as usize
    }

    /// Mischt eine Liste (Fisher-Yates)
    pub fn shuffle<T>(&mut self, items: &mut [T]) {
        for i in (1..items.len()).rev() {
            let j = self.index(i + 1);
            items.swap(i, j);
        }
    }
}

/// Ein Trainingsbeispiel.
pub struct Sample {
    pub pixels: Vec<f32>,
    pub rel_height: f32,
    pub label: u32,
}

/// Lädt alle .ttf / .otf Dateien aus einem Ordner.
pub fn load_fonts(dir: &Path) -> Result<Vec<FontVec>, String> {
    let entries = std::fs::read_dir(dir).map_err(|e| format!("{}: {}", dir.display(), e))?;
    let mut fonts = Vec::new();
    for entry in entries {
        let path = entry.map_err(|e| e.to_string())?.path();
        let ext = path
            .extension()
            .and_then(|e| e.to_str())
            .unwrap_or("")
            .to_ascii_lowercase();
        if ext != "ttf" && ext != "otf" {
            continue;
        }
        let bytes = std::fs::read(&path).map_err(|e| e.to_string())?;
        match FontVec::try_from_vec(bytes) {
            Ok(f) => fonts.push(f),
            Err(_) => println!("Uebersprungen (kein gueltiger Font): {}", path.display()),
        }
    }
    if fonts.is_empty() {
        return Err(format!("Keine .ttf/.otf Fonts in {}", dir.display()));
    }
    Ok(fonts)
}

/// Rendert ein Zeichen und bereitet es so auf wie `segment` es tun würde.
fn render_char(
    font: &FontVec,
    ch: char,
    size: f32,
    rot_deg: f32,
    threshold: u8,
    do_open: bool,
) -> Option<GrayImage> {
    let side = (size * 3.0) as u32;
    let mut canvas = GrayImage::new(side, side);
    draw_text_mut(
        &mut canvas,
        Luma([255u8]),
        size as i32,
        (size * 0.5) as i32,
        PxScale::from(size),
        font,
        &ch.to_string(),
    );

    let rotated = rotate_about_center(
        &canvas,
        rot_deg.to_radians(),
        Interpolation::Bilinear,
        Border::Constant(Luma([0u8])),
    );

    let mut bin = GrayImage::new(side, side);
    for (x, y, p) in rotated.enumerate_pixels() {
        bin.put_pixel(x, y, Luma([if p[0] > threshold { 255 } else { 0 }]));
    }

    let bin = if do_open {
        open(&bin, Norm::LInf, 1)
    } else {
        bin
    };
    largest_component_crop(&bin)
}

/// Erzeugt Trainingsdaten: pro Font `rounds` Durchgänge, jeder Durchgang
/// rendert alle 62 Zeichen mit zufälliger Größe, Drehung, Schwelle.
pub fn generate(fonts: &[FontVec], rounds: usize, rng: &mut Rng) -> Vec<Sample> {
    let mut samples = Vec::new();
    for font in fonts {
        for _ in 0..rounds {
            // Größe so gewählt, dass Großbuchstaben ca. 19-29 px hoch sind (wie im Captcha)
            let size = rng.range(30, 46) as f32;
            let rot = rng.float(-12.0, 12.0);
            let threshold = rng.range(90, 170) as u8;
            let do_open = rng.chance(0.8);

            let rendered: Vec<(u32, GrayImage)> = CHARS
                .chars()
                .enumerate()
                .filter_map(|(i, c)| {
                    render_char(font, c, size, rot, threshold, do_open).map(|m| (i as u32, m))
                })
                .collect();
            if rendered.len() < 5 {
                continue;
            }

            for (label, mask) in &rendered {
                // Relative Höhe wie im echten Captcha: gegen das höchste von
                // 5 Zeichen (dieses + 4 zufällige andere)
                let mut max_h = mask.height();
                for _ in 0..4 {
                    let other = &rendered[rng.index(rendered.len())].1;
                    max_h = max_h.max(other.height());
                }
                samples.push(Sample {
                    pixels: normalize(mask),
                    rel_height: mask.height() as f32 / max_h as f32,
                    label: *label,
                });
            }
        }
    }
    samples
}
