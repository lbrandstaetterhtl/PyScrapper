//! Python-Schnittstelle. Python sieht nur diese zwei Funktionen:
//!
//!   captcha_ocr.train(fonts_dir, model_path, rounds=40, epochs=8) -> float
//!   captcha_ocr.img_to_text(captcha_path, model_path, count=3) -> list[str]

mod features;
mod model;
mod segment;
mod synth;
mod trainer;

use pyo3::exceptions::{PyIOError, PyRuntimeError};
use pyo3::prelude::*;

/// Trainiert das Modell auf Zeichen aus den Fonts im Ordner `fonts_dir`
/// und speichert es unter `model_path` (.safetensors).
/// Gibt die Trainings-Genauigkeit zurück.
#[pyfunction]
#[pyo3(signature = (fonts_dir, model_path, rounds=40, epochs=8))]
fn train(fonts_dir: &str, model_path: &str, rounds: usize, epochs: usize) -> PyResult<f32> {
    trainer::train(fonts_dir, model_path, rounds, epochs).map_err(PyRuntimeError::new_err)
}

/// Liest ein Captcha und gibt die `count` wahrscheinlichsten Lesarten zurück,
/// die beste zuerst. Python bekommt eine Liste von Strings.
#[pyfunction]
#[pyo3(signature = (captcha_path, model_path, count=3))]
fn img_to_text(captcha_path: &str, model_path: &str, count: usize) -> PyResult<Vec<String>> {
    let img = image::open(captcha_path)
        .map_err(|e| PyIOError::new_err(format!("{}: {}", captcha_path, e)))?
        .to_rgb8();
    let ocr = trainer::Ocr::load(model_path).map_err(PyIOError::new_err)?;
    ocr.read_top(&img, count.max(1))
        .map_err(PyRuntimeError::new_err)
}

#[pymodule]
fn captcha_ocr(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(train, m)?)?;
    m.add_function(wrap_pyfunction!(img_to_text, m)?)?;
    Ok(())
}
