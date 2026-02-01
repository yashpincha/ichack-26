import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { invoke } from '@tauri-apps/api/core';
import UsageStats from '../../components/UsageStats';

// Mock the invoke function
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

const mockInvoke = invoke as ReturnType<typeof vi.fn>;

describe('UsageStats Component', () => {
  const mockStats = {
    total_requests: 150,
    total_prompt_tokens: 50000,
    total_completion_tokens: 25000,
    total_cost: 0.0125,
    by_provider: {
      openai: {
        request_count: 100,
        prompt_tokens: 40000,
        completion_tokens: 20000,
        total_cost: 0.01,
      },
      groq: {
        request_count: 50,
        prompt_tokens: 10000,
        completion_tokens: 5000,
        total_cost: 0.0,
      },
    },
    cache_hits: 75,
    cache_misses: 150,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockInvoke.mockResolvedValue(mockStats);
  });

  // ============ Loading State Tests ============

  describe('Loading State', () => {
    it('shows loading state initially', () => {
      mockInvoke.mockImplementation(() => new Promise(() => {})); // Never resolves
      render(<UsageStats />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  // ============ Data Display Tests ============

  describe('Data Display', () => {
    it('displays total requests', async () => {
      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('150')).toBeInTheDocument();
      });
    });

    it('displays total cost', async () => {
      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('$0.0125')).toBeInTheDocument();
      });
    });

    it('displays prompt tokens', async () => {
      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('50,000')).toBeInTheDocument();
      });
    });

    it('displays completion tokens', async () => {
      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('25,000')).toBeInTheDocument();
      });
    });

    it('displays cache hit rate', async () => {
      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('33.3%')).toBeInTheDocument(); // 75 / (75 + 150)
      });
    });

    it('displays cache hits and misses', async () => {
      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('75 / 150')).toBeInTheDocument();
      });
    });
  });

  // ============ Provider Breakdown Tests ============

  describe('Provider Breakdown', () => {
    it('displays provider table', async () => {
      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('By Provider')).toBeInTheDocument();
      });
    });

    it('displays openai stats', async () => {
      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('openai')).toBeInTheDocument();
        expect(screen.getByText('100')).toBeInTheDocument();
      });
    });

    it('displays groq stats', async () => {
      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('groq')).toBeInTheDocument();
        expect(screen.getByText('50')).toBeInTheDocument();
      });
    });
  });

  // ============ Average Cost Tests ============

  describe('Average Cost', () => {
    it('displays average cost per request', async () => {
      render(<UsageStats />);
      await waitFor(() => {
        // 0.0125 / 150 ≈ 0.000083
        expect(screen.getByText(/Avg cost per request/)).toBeInTheDocument();
      });
    });
  });

  // ============ Clear Stats Tests ============

  describe('Clear Stats', () => {
    it('renders clear stats button', async () => {
      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('Clear Stats')).toBeInTheDocument();
      });
    });

    it('calls clear_usage_stats when clicked', async () => {
      mockInvoke.mockImplementation((cmd: string) => {
        if (cmd === 'get_usage_stats') return Promise.resolve(mockStats);
        if (cmd === 'clear_usage_stats') return Promise.resolve();
        return Promise.resolve();
      });

      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('Clear Stats')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Clear Stats'));

      await waitFor(() => {
        expect(mockInvoke).toHaveBeenCalledWith('clear_usage_stats');
      });
    });
  });

  // ============ Error State Tests ============

  describe('Error State', () => {
    it('displays error message on failure', async () => {
      mockInvoke.mockRejectedValue('Failed to load stats');
      render(<UsageStats />);
      
      await waitFor(() => {
        expect(screen.getByText(/Error: Failed to load stats/)).toBeInTheDocument();
      });
    });
  });

  // ============ Empty Stats Tests ============

  describe('Empty Stats', () => {
    it('handles zero requests', async () => {
      mockInvoke.mockResolvedValue({
        ...mockStats,
        total_requests: 0,
        total_cost: 0,
        cache_hits: 0,
        cache_misses: 0,
        by_provider: {},
      });

      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('0')).toBeInTheDocument();
      });
    });

    it('shows N/A for cache hit rate when no cache activity', async () => {
      mockInvoke.mockResolvedValue({
        ...mockStats,
        cache_hits: 0,
        cache_misses: 0,
      });

      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('N/A')).toBeInTheDocument();
      });
    });
  });

  // ============ Cost Formatting Tests ============

  describe('Cost Formatting', () => {
    it('formats zero cost correctly', async () => {
      mockInvoke.mockResolvedValue({
        ...mockStats,
        total_cost: 0,
        by_provider: {}, // Clear providers to avoid multiple $0.00 elements
      });

      render(<UsageStats />);
      await waitFor(() => {
        // Find the Total Cost card specifically
        const costCard = screen.getByText('Total Cost').parentElement;
        expect(costCard?.querySelector('.usage-value')?.textContent).toBe('$0.00');
      });
    });

    it('formats small costs with more precision', async () => {
      mockInvoke.mockResolvedValue({
        ...mockStats,
        total_cost: 0.000001,
        by_provider: {}, // Clear providers to simplify
      });

      render(<UsageStats />);
      await waitFor(() => {
        expect(screen.getByText('$0.000001')).toBeInTheDocument();
      });
    });
  });
});
