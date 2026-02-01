import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { invoke } from '@tauri-apps/api/core';
import { useAutocomplete } from '../../hooks/useAutocomplete';

// Mock the invoke function
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

const mockInvoke = invoke as ReturnType<typeof vi.fn>;

describe('useAutocomplete Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ============ Initial State Tests ============

  describe('Initial State', () => {
    it('returns null suggestion initially', () => {
      const { result } = renderHook(() => useAutocomplete(''));
      
      expect(result.current.suggestion).toBeNull();
      expect(result.current.explanation).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('provides clearSuggestion function', () => {
      const { result } = renderHook(() => useAutocomplete(''));
      
      expect(typeof result.current.clearSuggestion).toBe('function');
    });
  });

  // ============ Input Length Tests ============

  describe('Input Length', () => {
    it('does not fetch for empty input', async () => {
      renderHook(() => useAutocomplete(''));
      
      await act(async () => {
        vi.advanceTimersByTime(500);
      });
      
      expect(mockInvoke).not.toHaveBeenCalled();
    });

    it('does not fetch for single character input', async () => {
      renderHook(() => useAutocomplete('g'));
      
      await act(async () => {
        vi.advanceTimersByTime(500);
      });
      
      expect(mockInvoke).not.toHaveBeenCalled();
    });

    it('fetches for input with 2+ characters', async () => {
      mockInvoke.mockResolvedValue({ completion: 'it status', explanation: null });
      
      renderHook(() => useAutocomplete('gi'));
      
      await act(async () => {
        vi.advanceTimersByTime(500);
      });
      
      expect(mockInvoke).toHaveBeenCalledWith('get_suggestion', { currentInput: 'gi' });
    });
  });

  // ============ Debounce Tests ============

  describe('Debouncing', () => {
    it('debounces requests', async () => {
      mockInvoke.mockResolvedValue({ completion: 'test', explanation: null });
      
      const { rerender } = renderHook(
        ({ input }) => useAutocomplete(input),
        { initialProps: { input: 'gi' } }
      );
      
      // Change input rapidly
      rerender({ input: 'git' });
      rerender({ input: 'git ' });
      rerender({ input: 'git s' });
      
      // Should not have called invoke yet
      expect(mockInvoke).not.toHaveBeenCalled();
      
      // Wait for debounce
      await act(async () => {
        vi.advanceTimersByTime(300);
      });
      
      // Should only call once with final input
      expect(mockInvoke).toHaveBeenCalledTimes(1);
      expect(mockInvoke).toHaveBeenCalledWith('get_suggestion', { currentInput: 'git s' });
    });

    it('cancels pending request when input changes', async () => {
      mockInvoke.mockResolvedValue({ completion: 'test', explanation: null });
      
      const { rerender } = renderHook(
        ({ input }) => useAutocomplete(input),
        { initialProps: { input: 'git' } }
      );
      
      // Advance partway through debounce
      await act(async () => {
        vi.advanceTimersByTime(100);
      });
      
      // Change input
      rerender({ input: 'npm' });
      
      // Advance through original debounce time
      await act(async () => {
        vi.advanceTimersByTime(200);
      });
      
      // Should not have called for 'git'
      expect(mockInvoke).not.toHaveBeenCalledWith('get_suggestion', { currentInput: 'git' });
      
      // Wait for new debounce
      await act(async () => {
        vi.advanceTimersByTime(100);
      });
      
      // Should call for 'npm'
      expect(mockInvoke).toHaveBeenCalledWith('get_suggestion', { currentInput: 'npm' });
    });
  });

  // ============ Suggestion Updates Tests ============

  describe('Suggestion Updates', () => {
    it('updates suggestion on successful response', async () => {
      mockInvoke.mockResolvedValue({ completion: ' status', explanation: 'Check repo status' });
      
      const { result } = renderHook(() => useAutocomplete('git'));
      
      await act(async () => {
        vi.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(result.current.suggestion).toBe(' status');
        expect(result.current.explanation).toBe('Check repo status');
      });
    });

    it('clears suggestion when response is empty', async () => {
      mockInvoke.mockResolvedValue({ completion: '', explanation: null });
      
      const { result } = renderHook(() => useAutocomplete('xyz'));
      
      await act(async () => {
        vi.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(result.current.suggestion).toBeNull();
      });
    });

    it('clears suggestion when response is whitespace only', async () => {
      mockInvoke.mockResolvedValue({ completion: '   ', explanation: null });
      
      const { result } = renderHook(() => useAutocomplete('xyz'));
      
      await act(async () => {
        vi.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(result.current.suggestion).toBeNull();
      });
    });
  });

  // ============ Loading State Tests ============

  describe('Loading State', () => {
    it('sets isLoading to true while fetching', async () => {
      let resolvePromise: (value: any) => void;
      mockInvoke.mockImplementation(() => new Promise(resolve => {
        resolvePromise = resolve;
      }));
      
      const { result } = renderHook(() => useAutocomplete('git'));
      
      await act(async () => {
        vi.advanceTimersByTime(300);
      });

      expect(result.current.isLoading).toBe(true);
      
      await act(async () => {
        resolvePromise!({ completion: 'test', explanation: null });
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  // ============ Error Handling Tests ============

  describe('Error Handling', () => {
    it('sets error on failure', async () => {
      mockInvoke.mockRejectedValue('API Error');
      
      const { result } = renderHook(() => useAutocomplete('git'));
      
      await act(async () => {
        vi.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(result.current.error).toBe('API Error');
        expect(result.current.suggestion).toBeNull();
      });
    });

    it('clears error on successful request', async () => {
      mockInvoke.mockRejectedValueOnce('API Error');
      mockInvoke.mockResolvedValueOnce({ completion: 'test', explanation: null });
      
      const { result, rerender } = renderHook(
        ({ input }) => useAutocomplete(input),
        { initialProps: { input: 'git' } }
      );
      
      // First request fails
      await act(async () => {
        vi.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(result.current.error).toBe('API Error');
      });
      
      // Change input to trigger new request
      rerender({ input: 'npm' });
      
      await act(async () => {
        vi.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });
    });
  });

  // ============ clearSuggestion Tests ============

  describe('clearSuggestion', () => {
    it('clears suggestion when called', async () => {
      mockInvoke.mockResolvedValue({ completion: 'test', explanation: 'Test explanation' });
      
      const { result } = renderHook(() => useAutocomplete('git'));
      
      await act(async () => {
        vi.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(result.current.suggestion).toBe('test');
      });
      
      act(() => {
        result.current.clearSuggestion();
      });
      
      expect(result.current.suggestion).toBeNull();
      expect(result.current.explanation).toBeNull();
    });

    it('cancels pending requests when called', async () => {
      mockInvoke.mockResolvedValue({ completion: 'test', explanation: null });
      
      const { result } = renderHook(() => useAutocomplete('git'));
      
      // Call clearSuggestion before debounce completes
      act(() => {
        result.current.clearSuggestion();
      });
      
      await act(async () => {
        vi.advanceTimersByTime(300);
      });
      
      // Should not have been called because we cleared
      expect(result.current.suggestion).toBeNull();
    });
  });

  // ============ Same Input Tests ============

  describe('Same Input', () => {
    it('does not refetch for same input', async () => {
      mockInvoke.mockResolvedValue({ completion: 'test', explanation: null });
      
      const { rerender } = renderHook(
        ({ input }) => useAutocomplete(input),
        { initialProps: { input: 'git' } }
      );
      
      await act(async () => {
        vi.advanceTimersByTime(300);
      });
      
      expect(mockInvoke).toHaveBeenCalledTimes(1);
      
      // Rerender with same input
      rerender({ input: 'git' });
      
      await act(async () => {
        vi.advanceTimersByTime(300);
      });
      
      // Should still only be 1 call
      expect(mockInvoke).toHaveBeenCalledTimes(1);
    });
  });
});
