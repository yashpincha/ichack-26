mod client;
mod providers;
mod prompt;

pub use client::get_completion;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Suggestion {
    pub completion: String,
    pub explanation: Option<String>,
}

impl Default for Suggestion {
    fn default() -> Self {
        Self {
            completion: String::new(),
            explanation: None,
        }
    }
}
