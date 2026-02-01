import { memo, useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';

interface ProviderUsage {
  request_count: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_cost: number;
}

interface UsageStatsData {
  total_requests: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_cost: number;
  by_provider: Record<string, ProviderUsage>;
  cache_hits: number;
  cache_misses: number;
}

interface UsageStatsProps {
  onClose?: () => void;
}

function UsageStats({ onClose }: UsageStatsProps) {
  const [stats, setStats] = useState<UsageStatsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setIsLoading(true);
      const data = await invoke<UsageStatsData>('get_usage_stats');
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err as string);
    } finally {
      setIsLoading(false);
    }
  };

  const clearStats = async () => {
    try {
      await invoke('clear_usage_stats');
      await fetchStats();
    } catch (err) {
      setError(err as string);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const formatCost = (cost: number): string => {
    if (cost === 0) return '$0.00';
    if (cost < 0.01) return `$${cost.toFixed(6)}`;
    return `$${cost.toFixed(4)}`;
  };

  const formatNumber = (num: number): string => {
    return num.toLocaleString();
  };

  const getCacheHitRate = (): string => {
    if (!stats) return '0%';
    const total = stats.cache_hits + stats.cache_misses;
    if (total === 0) return 'N/A';
    return `${((stats.cache_hits / total) * 100).toFixed(1)}%`;
  };

  if (isLoading) {
    return (
      <div className="usage-stats">
        <div className="usage-header">
          <h3>Usage Statistics</h3>
        </div>
        <div className="usage-loading">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="usage-stats">
        <div className="usage-header">
          <h3>Usage Statistics</h3>
        </div>
        <div className="usage-error">Error: {error}</div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="usage-stats">
      <div className="usage-header">
        <h3>Usage Statistics</h3>
        <button className="btn btn-small btn-secondary" onClick={clearStats}>
          Clear Stats
        </button>
      </div>

      <div className="usage-grid">
        <div className="usage-card">
          <div className="usage-label">Total Requests</div>
          <div className="usage-value">{formatNumber(stats.total_requests)}</div>
        </div>

        <div className="usage-card">
          <div className="usage-label">Total Cost</div>
          <div className="usage-value cost">{formatCost(stats.total_cost)}</div>
        </div>

        <div className="usage-card">
          <div className="usage-label">Prompt Tokens</div>
          <div className="usage-value">{formatNumber(stats.total_prompt_tokens)}</div>
        </div>

        <div className="usage-card">
          <div className="usage-label">Completion Tokens</div>
          <div className="usage-value">{formatNumber(stats.total_completion_tokens)}</div>
        </div>

        <div className="usage-card">
          <div className="usage-label">Cache Hit Rate</div>
          <div className="usage-value">{getCacheHitRate()}</div>
        </div>

        <div className="usage-card">
          <div className="usage-label">Cache Hits / Misses</div>
          <div className="usage-value">{stats.cache_hits} / {stats.cache_misses}</div>
        </div>
      </div>

      {Object.keys(stats.by_provider).length > 0 && (
        <div className="usage-by-provider">
          <h4>By Provider</h4>
          <table className="usage-table">
            <thead>
              <tr>
                <th>Provider</th>
                <th>Requests</th>
                <th>Tokens</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(stats.by_provider).map(([provider, usage]) => (
                <tr key={provider}>
                  <td>{provider}</td>
                  <td>{formatNumber(usage.request_count)}</td>
                  <td>{formatNumber(usage.prompt_tokens + usage.completion_tokens)}</td>
                  <td>{formatCost(usage.total_cost)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {stats.total_requests > 0 && (
        <div className="usage-footer">
          <span>Avg cost per request: {formatCost(stats.total_cost / stats.total_requests)}</span>
        </div>
      )}
    </div>
  );
}

export default memo(UsageStats);
