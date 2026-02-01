use std::collections::HashMap;
use std::time::{Duration, Instant};

use crate::llm::Suggestion;

const CACHE_TTL_SECS: u64 = 300; // 5 minutes
const MAX_CACHE_SIZE: usize = 100;

struct CacheEntry {
    suggestion: Suggestion,
    created_at: Instant,
}

pub struct SuggestionCache {
    entries: HashMap<String, CacheEntry>,
}

impl SuggestionCache {
    pub fn new() -> Self {
        Self {
            entries: HashMap::new(),
        }
    }
    
    pub fn get(&self, input: &str) -> Option<Suggestion> {
        if let Some(entry) = self.entries.get(input) {
            // Check if entry is still valid
            if entry.created_at.elapsed() < Duration::from_secs(CACHE_TTL_SECS) {
                return Some(entry.suggestion.clone());
            }
        }
        None
    }
    
    pub fn set(&mut self, input: &str, suggestion: Suggestion) {
        // Evict old entries if cache is full
        if self.entries.len() >= MAX_CACHE_SIZE {
            self.evict_oldest();
        }
        
        // Also evict expired entries
        self.evict_expired();
        
        self.entries.insert(
            input.to_string(),
            CacheEntry {
                suggestion,
                created_at: Instant::now(),
            },
        );
    }
    
    fn evict_oldest(&mut self) {
        if let Some(oldest_key) = self
            .entries
            .iter()
            .min_by_key(|(_, v)| v.created_at)
            .map(|(k, _)| k.clone())
        {
            self.entries.remove(&oldest_key);
        }
    }
    
    fn evict_expired(&mut self) {
        let now = Instant::now();
        let ttl = Duration::from_secs(CACHE_TTL_SECS);
        
        self.entries.retain(|_, entry| now.duration_since(entry.created_at) < ttl);
    }
    
    #[allow(dead_code)]
    pub fn clear(&mut self) {
        self.entries.clear();
    }
}

impl Default for SuggestionCache {
    fn default() -> Self {
        Self::new()
    }
}
