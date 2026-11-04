use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use candle_core::Device;

#[derive(Serialize, Deserialize)]
pub struct Config {
    pub kernel_size: usize,
    pub conv_count: u32,
    pub input_size: usize,
    pub vocab_str: String,
    pub pool_after: Vec<bool>,
    pub model_name: String,
    pub device: String,
    pub max_candidates: usize
}

impl Config {
    pub fn default() -> Self {
        Config {kernel_size: 3, conv_count: 3, input_size: 28, vocab_str: "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz".to_string(), pool_after: vec![true, true, false], model_name: "model.safetensors".to_string(), device: "cpu".to_string(), max_candidates: 3}
    }

    pub fn load(path: &str) -> Result<Self, String> {
        let config_name = "config.json";
        let config_path = Path::new(path).join(config_name);
       if !config_path.exists() {
           let config = Config::default();
           match config.save(config_path.as_path().to_str().unwrap()) {
               Ok(_) => Ok(config),
               Err(e) => Err(format!("[ocr] Could not save default generated config: {}", e.to_string()).to_string())
           }
       }
        else {
            let json = fs::read_to_string(config_path).map_err(|e| format!("[ocr] Could not read config file: {}", e))?;
            let config = serde_json::from_str::<Config>(&json).map_err(|e| format!("[ocr] Could not parse config file: {}", e))?;
            Ok(config)
        }
    }

    pub fn device(&self) -> Result<Device, String> {
        match self.device.as_str() {
            "cpu" => Ok(Device::Cpu),
            "cuda" => Device::new_cuda(0).map_err(|e| e.to_string()),
            "metal" => Device::new_metal(0).map_err(|e| e.to_string()),
            other => Err(format!("[ocr] unknown device: {}", other)),
        }
    }

    pub fn save(&self, path: &str) -> Result<(), String> {
        let str = serde_json::to_string_pretty(self).unwrap();
        match fs::write(path, str) {
            Ok(_) => Ok(()),
            Err(_) => Err(format!("[ocr] Could not save config: {}", path))
        }
    }
}