import { useState, useEffect, useRef, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

interface Suggestion {
  completion: string;
  explanation: string | null;
}

interface UseAutocompleteResult {
  suggestion: string | null;
  explanation: string | null;
  isLoading: boolean;
  error: string | null;
  clearSuggestion: () => void;
}

const DEFAULT_DEBOUNCE_MS = 300;
const MIN_INPUT_LENGTH = 2;

export function useAutocomplete(input: string): UseAutocompleteResult {
  const [suggestion, setSuggestion] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const debounceTimerRef = useRef<number | null>(null);
  const lastInputRef = useRef<string>('');
  const abortControllerRef = useRef<AbortController | null>(null);

  const clearSuggestion = useCallback(() => {
    setSuggestion(null);
    setExplanation(null);
    setError(null);
    
    // Cancel any pending request
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  const fetchSuggestion = useCallback(async (currentInput: string) => {
    // Skip if input is too short
    if (currentInput.trim().length < MIN_INPUT_LENGTH) {
      setSuggestion(null);
      return;
    }

    // Skip if input hasn't changed
    if (currentInput === lastInputRef.current) {
      return;
    }

    lastInputRef.current = currentInput;
    setIsLoading(true);
    setError(null);

    try {
      const result = await invoke<Suggestion>('get_suggestion', {
        currentInput,
      });

      // Only update if the input hasn't changed while we were waiting
      if (currentInput === lastInputRef.current) {
        if (result.completion && result.completion.trim()) {
          setSuggestion(result.completion);
          setExplanation(result.explanation);
        } else {
          setSuggestion(null);
          setExplanation(null);
        }
      }
    } catch (err) {
      console.error('Autocomplete error:', err);
      if (currentInput === lastInputRef.current) {
        setError(err as string);
        setSuggestion(null);
      }
    } finally {
      if (currentInput === lastInputRef.current) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // If input is empty or too short, clear suggestion
    if (!input || input.trim().length < MIN_INPUT_LENGTH) {
      setSuggestion(null);
      setExplanation(null);
      setIsLoading(false);
      return;
    }

    // Debounce the request
    debounceTimerRef.current = window.setTimeout(() => {
      fetchSuggestion(input);
    }, DEFAULT_DEBOUNCE_MS);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [input, fetchSuggestion]);

  return {
    suggestion,
    explanation,
    isLoading,
    error,
    clearSuggestion,
  };
}
