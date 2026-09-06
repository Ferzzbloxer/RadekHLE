pub struct Corruptor {
    enabled: bool,
    frames: u64,
}

impl Corruptor {
    pub fn new(enabled: bool) -> Self {
        Self { enabled, frames: 0 }
    }

    pub fn tick(&mut self) {
        if !self.enabled {
            return;
        }
        self.frames = self.frames.wrapping_add(1);
        if self.frames % 1800 == 0 {
            log_dbg!("[RTCS] safe presentation-only corruption remains active after {} frames", self.frames);
        }
    }
}
