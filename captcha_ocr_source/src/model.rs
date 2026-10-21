//! Das neuronale Netz (CNN) mit candle.
//!
//! Eingabe:  Bild 1 x 28 x 28  +  relative Höhe (1 Zahl)
//! Ausgabe:  62 Werte, einer pro Zeichen; der größte ist die Vorhersage

use crate::features::{N, NUM_CLASSES};
use candle_core::{Device, Module, Result, Tensor};
use candle_nn::{conv2d, linear, Conv2d, Conv2dConfig, Linear, VarBuilder};

pub struct Net {
    conv1: Conv2d,
    conv2: Conv2d,
    fc1: Linear,
    fc2: Linear,
}

fn conv_cfg() -> Conv2dConfig {
    Conv2dConfig {
        padding: 1,
        ..Default::default()
    }
}

impl Net {
    pub fn new(vb: VarBuilder) -> Result<Self> {
        // nach 2x Pooling: 28 -> 14 -> 7
        let flat = 64 * (N as usize / 4) * (N as usize / 4);
        Ok(Self {
            conv1: conv2d(1, 32, 3, conv_cfg(), vb.pp("conv1"))?,
            conv2: conv2d(32, 64, 3, conv_cfg(), vb.pp("conv2"))?,
            fc1: linear(flat + 1, 128, vb.pp("fc1"))?,
            fc2: linear(128, NUM_CLASSES, vb.pp("fc2"))?,
        })
    }

    /// x: (Batch, 1, N, N)   rel: (Batch, 1)   ->   (Batch, 62)
    pub fn forward(&self, x: &Tensor, rel: &Tensor) -> Result<Tensor> {
        let x = self.conv1.forward(x)?.relu()?.max_pool2d(2)?;
        let x = self.conv2.forward(&x)?.relu()?.max_pool2d(2)?;
        let x = x.flatten_from(1)?;
        let x = Tensor::cat(&[&x, rel], 1)?;
        let x = self.fc1.forward(&x)?.relu()?;
        self.fc2.forward(&x)
    }
}

/// Packt mehrere Zeichen in die Tensoren, die `forward` erwartet.
pub fn to_tensors(pixels: &[&[f32]], rel: &[f32], dev: &Device) -> Result<(Tensor, Tensor)> {
    let b = pixels.len();
    let flat: Vec<f32> = pixels.iter().flat_map(|p| p.iter().copied()).collect();
    let x = Tensor::from_vec(flat, (b, 1, N as usize, N as usize), dev)?;
    let r = Tensor::from_vec(rel.to_vec(), (b, 1), dev)?;
    Ok((x, r))
}
