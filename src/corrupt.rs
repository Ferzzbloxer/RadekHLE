use crate::mem::{GuestUSize, Mem};

pub struct Corruptor {
    enabled: bool,
    state: u64,
    frames: u64,
    total: u64,
}

impl Corruptor {
    pub fn new(enabled: bool) -> Self {
        Self { enabled, state: 0x6a09e667f3bcc909, frames: 0, total: 0 }
    }

    pub fn tick(&mut self, mem: &mut Mem) {
        if !self.enabled {
            return;
        }
        self.frames = self.frames.wrapping_add(1);
        let interval = (240u64).saturating_sub((self.frames / 1800).min(180));
        if self.frames % interval.max(30) != 0 {
            return;
        }
        let allocations = mem.live_allocations();
        if allocations.is_empty() {
            return;
        }
        let mut budget = 1 + (self.frames / 3600).min(7) as u32;
        for &(base, size) in &allocations {
            if budget == 0 {
                break;
            }
            if size < 32 {
                continue;
            }
            let offset = 16 + (self.next() % (size.saturating_sub(16) as u64)) as GuestUSize;
            let value = self.next() as u8;
            if mem.corrupt_byte(base.saturating_add(offset), value) {
                self.total += 1;
                budget -= 1;
            }
        }
        if self.total != 0 {
            log_dbg!("[RTCS] safely corrupted {} byte(s) in live guest allocations", self.total);
        }
    }

    fn next(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9e3779b97f4a7c15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
        z ^ (z >> 31)
    }
}
