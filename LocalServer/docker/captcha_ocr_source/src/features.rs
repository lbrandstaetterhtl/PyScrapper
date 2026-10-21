//! Bringt eine Zeichen-Maske in die feste Form, die das Netz erwartet.

use image::imageops::{self, FilterType};
use image::GrayImage;

/// Alle Zeichen, die erkannt werden können. Index = Klassen-Nummer im Netz.
pub const CHARS: &str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
pub const NUM_CLASSES: usize = 62;

/// Kantenlänge des Netz-Eingabebildes (N x N).
pub const N: u32 = 28;

/// Buchstaben, die groß und klein dieselbe Form haben.
/// Hier entscheidet nur die Höhe, nicht das Netz.
const SAME_SHAPE: &str = "cosuvwxz";
/// Ab dieser relativen Höhe gilt so ein Buchstabe als Großbuchstabe.
/// Gemessen an echten Captchas: Klein 0.67-0.82, Groß 0.87-1.0.
const CAPITAL_REL: f32 = 0.85;

/// Maske -> zentriert in Quadrat -> N x N -> Werte 0.0..1.0
pub fn normalize(mask: &GrayImage) -> Vec<f32> {
    let (w, h) = mask.dimensions();
    let s = w.max(h);
    let mut square = GrayImage::new(s, s);
    let ox = (s - w) / 2;
    let oy = (s - h) / 2;
    for (x, y, p) in mask.enumerate_pixels() {
        square.put_pixel(x + ox, y + oy, *p);
    }
    let small = imageops::resize(&square, N, N, FilterType::Triangle);
    small.pixels().map(|p| p[0] as f32 / 255.0).collect()
}

/// Höhe jedes Zeichens relativ zum höchsten Zeichen im selben Captcha.
pub fn relative_heights(masks: &[GrayImage]) -> Vec<f32> {
    let max_h = masks.iter().map(|m| m.height()).max().unwrap_or(1) as f32;
    masks.iter().map(|m| m.height() as f32 / max_h).collect()
}

/// Korrigiert Groß/Klein für Buchstaben mit gleicher Form anhand der Höhe.
pub fn fix_case(c: char, rel_height: f32) -> char {
    if SAME_SHAPE.contains(c.to_ascii_lowercase()) {
        if rel_height >= CAPITAL_REL {
            c.to_ascii_uppercase()
        } else {
            c.to_ascii_lowercase()
        }
    } else {
        c
    }
}

/// Klassen-Nummer -> Zeichen
pub fn class_to_char(class: u32) -> char {
    CHARS.as_bytes()[class as usize] as char
}
