import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import FixSuggestion from '../../components/FixSuggestion';

describe('FixSuggestion Component', () => {
  const defaultProps = {
    errorContext: {
      command: 'gti status',
      exit_code: 127,
      output: 'command not found: gti',
    },
    suggestion: {
      fixed_command: 'git status',
      explanation: 'Fixed typo: "gti" should be "git"',
      confidence: 'high',
    },
    onApply: vi.fn(),
    onDismiss: vi.fn(),
    isLoading: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============ Rendering Tests ============

  describe('Rendering', () => {
    it('renders the modal', () => {
      render(<FixSuggestion {...defaultProps} />);
      expect(screen.getByText('Fix Error Please (FEP)')).toBeInTheDocument();
    });

    it('displays the failed command', () => {
      render(<FixSuggestion {...defaultProps} />);
      expect(screen.getByText('gti status')).toBeInTheDocument();
    });

    it('displays the exit code', () => {
      render(<FixSuggestion {...defaultProps} />);
      expect(screen.getByText('Exit code: 127')).toBeInTheDocument();
    });

    it('displays the error output', () => {
      render(<FixSuggestion {...defaultProps} />);
      expect(screen.getByText('command not found: gti')).toBeInTheDocument();
    });

    it('displays the suggested fix', () => {
      render(<FixSuggestion {...defaultProps} />);
      expect(screen.getByText('git status')).toBeInTheDocument();
    });

    it('displays the explanation', () => {
      render(<FixSuggestion {...defaultProps} />);
      expect(screen.getByText('Fixed typo: "gti" should be "git"')).toBeInTheDocument();
    });
  });

  // ============ Loading State Tests ============

  describe('Loading State', () => {
    it('shows loading spinner when isLoading is true', () => {
      render(<FixSuggestion {...defaultProps} isLoading={true} />);
      expect(screen.getByText('Analyzing Error...')).toBeInTheDocument();
      expect(screen.getByText('Looking for a fix...')).toBeInTheDocument();
    });

    it('does not show suggestion content when loading', () => {
      render(<FixSuggestion {...defaultProps} isLoading={true} />);
      expect(screen.queryByText('git status')).not.toBeInTheDocument();
    });
  });

  // ============ Confidence Badge Tests ============

  describe('Confidence Badge', () => {
    it('shows HIGH confidence badge', () => {
      render(<FixSuggestion {...defaultProps} />);
      // Badge renders as "✓ HIGH" - use regex to find partial match
      expect(screen.getByText(/HIGH/)).toBeInTheDocument();
    });

    it('shows MEDIUM confidence badge', () => {
      render(<FixSuggestion {...defaultProps} suggestion={{ ...defaultProps.suggestion, confidence: 'medium' }} />);
      expect(screen.getByText(/MEDIUM/)).toBeInTheDocument();
    });

    it('shows LOW confidence badge', () => {
      render(<FixSuggestion {...defaultProps} suggestion={{ ...defaultProps.suggestion, confidence: 'low' }} />);
      expect(screen.getByText(/LOW/)).toBeInTheDocument();
    });

    it('shows checkmark for high confidence', () => {
      render(<FixSuggestion {...defaultProps} />);
      // The icon is part of the badge text "✓ HIGH"
      expect(screen.getByText(/✓/)).toBeInTheDocument();
    });
  });

  // ============ Button Tests ============

  describe('Button Actions', () => {
    it('calls onApply with fixed command when Apply Fix clicked', () => {
      render(<FixSuggestion {...defaultProps} />);
      
      fireEvent.click(screen.getByText('Apply Fix'));
      
      expect(defaultProps.onApply).toHaveBeenCalledWith('git status');
    });

    it('calls onDismiss when Dismiss clicked', () => {
      render(<FixSuggestion {...defaultProps} />);
      
      fireEvent.click(screen.getByText('Dismiss'));
      
      expect(defaultProps.onDismiss).toHaveBeenCalledTimes(1);
    });

    it('disables Apply Fix when no fixed command', () => {
      render(<FixSuggestion {...defaultProps} suggestion={{ ...defaultProps.suggestion, fixed_command: '' }} />);
      
      const applyButton = screen.getByText('Apply Fix');
      expect(applyButton).toBeDisabled();
    });
  });

  // ============ Hint Tests ============

  describe('Hint', () => {
    it('shows Ctrl+F hint', () => {
      render(<FixSuggestion {...defaultProps} />);
      expect(screen.getByText(/Ctrl\+F/)).toBeInTheDocument();
    });
  });

  // ============ Long Output Truncation Test ============

  describe('Output Truncation', () => {
    it('truncates long error output', () => {
      const longOutput = 'x'.repeat(600);
      render(<FixSuggestion {...defaultProps} errorContext={{ ...defaultProps.errorContext, output: longOutput }} />);
      
      expect(screen.getByText(/\.\.\./)).toBeInTheDocument();
    });
  });

  // ============ Wrench Icon Test ============

  describe('Icon', () => {
    it('shows wrench icon', () => {
      render(<FixSuggestion {...defaultProps} />);
      expect(screen.getByText('🔧')).toBeInTheDocument();
    });
  });
});
