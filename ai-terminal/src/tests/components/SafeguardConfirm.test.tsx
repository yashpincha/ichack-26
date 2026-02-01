import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SafeguardConfirm from '../../components/SafeguardConfirm';

describe('SafeguardConfirm Component', () => {
  const defaultProps = {
    command: 'chmod 777 /etc/passwd',
    safeguardResult: {
      is_dangerous: true,
      matched_pattern: 'chmod 777',
      description: 'World-writable permissions',
      severity: 'medium',
    },
    onProceed: vi.fn(),
    onCancel: vi.fn(),
    onDisableForSession: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============ Rendering Tests ============

  describe('Rendering', () => {
    it('renders the modal', () => {
      render(<SafeguardConfirm {...defaultProps} />);
      expect(screen.getByText('Command Safeguard')).toBeInTheDocument();
    });

    it('displays the command', () => {
      render(<SafeguardConfirm {...defaultProps} />);
      expect(screen.getByText('chmod 777 /etc/passwd')).toBeInTheDocument();
    });

    it('displays matched pattern', () => {
      render(<SafeguardConfirm {...defaultProps} />);
      expect(screen.getByText('chmod 777')).toBeInTheDocument();
    });

    it('displays description', () => {
      render(<SafeguardConfirm {...defaultProps} />);
      expect(screen.getByText('World-writable permissions')).toBeInTheDocument();
    });

    it('displays severity badge', () => {
      render(<SafeguardConfirm {...defaultProps} />);
      expect(screen.getByText('MEDIUM RISK')).toBeInTheDocument();
    });
  });

  // ============ Severity Tests ============

  describe('Severity Display', () => {
    it('shows critical severity', () => {
      render(<SafeguardConfirm {...defaultProps} safeguardResult={{ ...defaultProps.safeguardResult, severity: 'critical' }} />);
      expect(screen.getByText('CRITICAL RISK')).toBeInTheDocument();
    });

    it('shows high severity', () => {
      render(<SafeguardConfirm {...defaultProps} safeguardResult={{ ...defaultProps.safeguardResult, severity: 'high' }} />);
      expect(screen.getByText('HIGH RISK')).toBeInTheDocument();
    });

    it('shows low severity', () => {
      render(<SafeguardConfirm {...defaultProps} safeguardResult={{ ...defaultProps.safeguardResult, severity: 'low' }} />);
      expect(screen.getByText('LOW RISK')).toBeInTheDocument();
    });
  });

  // ============ Button Tests ============

  describe('Button Actions', () => {
    it('calls onProceed when Proceed button is clicked', () => {
      render(<SafeguardConfirm {...defaultProps} />);
      
      fireEvent.click(screen.getByText('I Understand, Proceed'));
      
      expect(defaultProps.onProceed).toHaveBeenCalledTimes(1);
    });

    it('calls onCancel when Cancel button is clicked', () => {
      render(<SafeguardConfirm {...defaultProps} />);
      
      fireEvent.click(screen.getByText('Cancel'));
      
      expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
    });

    it('Cancel button has autoFocus', () => {
      render(<SafeguardConfirm {...defaultProps} />);
      
      const cancelButton = screen.getByText('Cancel');
      expect(cancelButton).toHaveFocus();
    });
  });

  // ============ Don't Ask Again Checkbox Tests ============

  describe('Don\'t Ask Again Checkbox', () => {
    it('renders checkbox when onDisableForSession is provided', () => {
      render(<SafeguardConfirm {...defaultProps} />);
      expect(screen.getByText("Don't ask again this session")).toBeInTheDocument();
    });

    it('does not render checkbox when onDisableForSession is not provided', () => {
      render(<SafeguardConfirm {...defaultProps} onDisableForSession={undefined} />);
      expect(screen.queryByText("Don't ask again this session")).not.toBeInTheDocument();
    });

    it('calls onDisableForSession when checked and proceed clicked', () => {
      render(<SafeguardConfirm {...defaultProps} />);
      
      const checkbox = screen.getByRole('checkbox');
      fireEvent.click(checkbox);
      
      fireEvent.click(screen.getByText('I Understand, Proceed'));
      
      expect(defaultProps.onDisableForSession).toHaveBeenCalledTimes(1);
      expect(defaultProps.onProceed).toHaveBeenCalledTimes(1);
    });

    it('does not call onDisableForSession when unchecked and proceed clicked', () => {
      render(<SafeguardConfirm {...defaultProps} />);
      
      fireEvent.click(screen.getByText('I Understand, Proceed'));
      
      expect(defaultProps.onDisableForSession).not.toHaveBeenCalled();
      expect(defaultProps.onProceed).toHaveBeenCalledTimes(1);
    });
  });

  // ============ Shield Icon Test ============

  describe('Icon', () => {
    it('shows shield icon', () => {
      render(<SafeguardConfirm {...defaultProps} />);
      expect(screen.getByText('🛡️')).toBeInTheDocument();
    });
  });

  // ============ No Pattern Match Test ============

  describe('No Pattern Match', () => {
    it('handles null matched_pattern', () => {
      render(<SafeguardConfirm {...defaultProps} safeguardResult={{ ...defaultProps.safeguardResult, matched_pattern: null }} />);
      expect(screen.queryByText('Matched Pattern:')).not.toBeInTheDocument();
    });
  });
});
