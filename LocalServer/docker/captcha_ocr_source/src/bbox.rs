#[derive(Debug, Clone, Copy)]
pub struct BBox {
    pub min_x: u32,
    pub min_y: u32,
    pub max_x: u32,
    pub max_y: u32,
    pub area: u32,
}

impl BBox {
    pub fn width(&self) -> u32 {
        self.max_x - self.min_x + 1
    }

    pub fn height(&self) -> u32 {
        self.max_y - self.min_y + 1
    }

    pub fn fill(&self) -> f32 {
        self.area as f32 / (self.width() * self.height()) as f32
    }
}