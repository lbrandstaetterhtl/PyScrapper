use std::collections::HashMap;
use std::path::Path;
use candle_core::{DType, Device, Module, Tensor};
use candle_nn::{conv2d, linear, Conv2d, Conv2dConfig, Linear, VarBuilder, VarMap};
use crate::config::Config;

pub struct CNN {
    pub var_map: VarMap,
    pub conv_list: Vec<Conv2d>,
    pub pool_after: Vec<bool>,
    pub fc: Linear,
    pub vocab: Vocab
}

pub struct Vocab {
    pub to_idx: HashMap<char, u32>,
    pub to_char: Vec<char>,
}

impl CNN {
    pub fn new(vocab: Vocab, var_builder: VarBuilder, pool_after: Vec<bool>, conv_count: u32, kernel_size: usize, input_size: usize, var_map: VarMap) -> Result<Self, String> {
        let config = Conv2dConfig {padding: 0, stride: 1, ..Default::default()};
        let mut conv_list: Vec<Conv2d> = Vec::new();
        let mut in_ch: usize = 1;
        let mut out_ch: usize = 16;
        let mut conv_counter: u32 = 0;
        let mut size = input_size;

        while conv_counter < conv_count {
            let conv = match conv2d(in_ch, out_ch, kernel_size, config, var_builder.pp(format!("conv{}", conv_counter))) {
                Ok(conv) => conv,
                Err(e) => return Err(e.to_string())
            };
            conv_list.push(conv);

            if size < kernel_size {
                return Err(format!("conv{} would need {}x{} but only {}x{} left", conv_counter, kernel_size, kernel_size, size, size));
            }
            size = size - kernel_size + 1;

            if pool_after[conv_counter as usize] {
                if size < 2 {
                    return Err(format!("pool after conv{} is impossible at size {}", conv_counter, size));
                }
                size /= 2;
            }

            in_ch = out_ch;
            out_ch *= 2;
            conv_counter += 1;
        }


        let flat = in_ch * size * size;
        let fc = match linear(flat, vocab.len(), var_builder.pp("fc")) {
            Ok(v) => v,
            Err(e) => return Err(e.to_string())
        };

        Ok(Self { var_map, conv_list, pool_after, fc, vocab })
    }

    pub fn forward(&self, tensor: &Tensor) -> Result<Tensor, String> {
        let mut step: Tensor = tensor.clone();
        let mut conv_counter: u32 = 0;

        while conv_counter < self.conv_list.len() as u32 {
            let conv = self.conv_list.get(conv_counter as usize).unwrap();

            step = match conv.forward(&step) {
                Ok(v) => v,
                Err(e) => return Err(e.to_string())
            };

            step = match step.relu() {
                Ok(v) => v,
                Err(e) => return Err(e.to_string())
            };

            if self.pool_after[conv_counter as usize] {
                step = match step.max_pool2d(2) {
                    Ok(v) => v,
                    Err(e) => return Err(e.to_string())
                }
            }

            conv_counter += 1;
        }

        step = match step.flatten_from(1) {
            Ok(v) => v,
            Err(e) => return Err(e.to_string())
        };

        let result = match self.fc.forward(&step) {
            Ok(v) => v,
            Err(e) => return Err(e.to_string())
        };

        Ok(result)
    }

    pub fn load(device: &Device, config: &Config, ocr_dir: &str) -> Result<Self, String> {
        let vocab = Vocab::new(config.vocab_str.as_str());
        let var_map = VarMap::new();
        let var_builder = VarBuilder::from_varmap(&var_map, DType::F32, device);

        let mut cnn = match Self::new(vocab, var_builder, config.pool_after.clone(), config.conv_count, config.kernel_size, config.input_size, var_map) {
            Ok(v) => v,
            Err(e) => return Err(e.to_string())
        };

        let model_path = Path::new(ocr_dir).join(config.model_name.clone());
        if model_path.exists() {
            if let Err(e) = cnn.var_map.load(model_path) {
                return Err(e.to_string());
            }
        }

        Ok(cnn)
    }

    pub fn save(&self, model_path: &str) -> Result<(), String> {

        let _ = match self.var_map.save(model_path) {
            Ok(v) => v,
            Err(e) => return Err(e.to_string())
        };

        Ok(())
    }

}

impl Vocab {
    pub fn new(chars: &str) -> Self {
        let to_char: Vec<char> = chars.chars().collect();
        let to_idx = to_char.iter().enumerate()
            .map(|(i, &c)| (c, i as u32))
            .collect();
        Self { to_idx, to_char }
    }

    pub fn encode(&self, c: char) -> Option<u32> {
        self.to_idx.get(&c).copied()
    }

    pub fn decode(&self, i: u32) -> char {
        self.to_char[i as usize]
    }

    pub fn len(&self) -> usize {
        self.to_char.len()
    }
}
