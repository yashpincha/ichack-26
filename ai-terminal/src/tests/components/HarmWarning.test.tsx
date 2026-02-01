import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import HarmWarning from '../../components/HarmWarning';

describe('HarmWarning Component', () => {
  const defaultProps = {
    command: 'rm -rf /',
    harmResult: {
      is_harmful: true,
      reason: 'This command will delete all files on the system',
      severity: 'critical',
    },
    onProceed: vi.fn(),
    onCancel: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============ Rendering Tests ============

  describe('Rendering', () => {
    it('renders the modal', () => {
      render(<HarmWarning {...defaultProps} />);
      expect(screen.getByText('Potentially Harmful Command Detected')).toBeInTheDocument();
    });

    it('displays the command', () => {
      render(<HarmWarning {...defaultProps} />);
      expect(screen.getByText('rm -rf /')).toBeInTheDocument();
    });

    it('displays the reason', () => {
      render(<HarmWarning {...defaultProps} />);
      expect(screen.getByText('This command will delete all files on the system')).toBeInTheDocument();
    });

    it('displays severity badge', () => {
      render(<HarmWarning {...defaultProps} />);
      expect(screen.getByText('CRITICAL RISK')).toBeInTheDocument();
    });
  });

  // ============ Severity Tests ============

  describe('Severity Display', () => {
    it('shows critical severity correctly', () => {
      render(<HarmWarning {...defaultProps} />);
      expect(screen.getByText('CRITICAL RISK')).toBeInTheDocument();
    });

    it('shows high severity correctly', () => {
      render(<HarmWarning {...defaultProps} harmResult={{ ...defaultProps.harmResult, severity: 'high' }} />);
      expect(screen.getByText('HIGH RISK')).toBeInTheDocument();
    });

    it('shows medium severity correctly', () => {
      render(<HarmWarning {...defaultProps} harmResult={{ ...defaultProps.harmResult, severity: 'medium' }} />);
      expect(screen.getByText('MEDIUM RISK')).toBeInTheDocument();
    });

    it('shows low severity correctly', () => {
      render(<HarmWarning {...defaultProps} harmResult={{ ...defaultProps.harmResult, severity: 'low' }} />);
      expect(screen.getByText('LOW RISK')).toBeInTheDocument();
    });
  });

  // ============ Button Tests ============

  describe('Button Actions', () => {
    it('calls onProceed when Proceed button is clicked', () => {
      render(<HarmWarning {...defaultProps} />);
      
      fireEvent.click(screen.getByText('Proceed Anyway'));
      
      expect(defaultProps.onProceed).toHaveBeenCalledTimes(1);
    });

    it('calls onCancel when Cancel button is clicked', () => {
      render(<HarmWarning {...defaultProps} />);
      
      fireEvent.click(screen.getByText('Cancel'));
      
      expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
    });

    it('Cancel button has autoFocus', () => {
      render(<HarmWarning {...defaultProps} />);
      
      const cancelButton = screen.getByText('Cancel');
      expect(cancelButton).toHaveFocus();
    });
  });

  // ============ Warning Content Tests ============

  describe('Warning Content', () => {
    it('displays warning about data loss', () => {
      render(<HarmWarning {...defaultProps} />);
      expect(screen.getByText(/Data loss or corruption/)).toBeInTheDocument();
    });

    it('displays warning about system instability', () => {
      render(<HarmWarning {...defaultProps} />);
      expect(screen.getByText(/System instability/)).toBeInTheDocument();
    });

    it('displays warning about security vulnerabilities', () => {
      render(<HarmWarning {...defaultProps} />);
      expect(screen.getByText(/Security vulnerabilities/)).toBeInTheDocument();
    });
  });

  // ============ Icon Tests ============

  describe('Severity Icons', () => {
    it('shows stop icon for critical severity', () => {
      render(<HarmWarning {...defaultProps} />);
      expect(screen.getByText('⛔')).toBeInTheDocument();
    });

    it('shows alert icon for high severity', () => {
      render(<HarmWarning {...defaultProps} harmResult={{ ...defaultProps.harmResult, severity: 'high' }} />);
      expect(screen.getByText('🚨')).toBeInTheDocument();
    });

    it('shows warning icon for medium severity', () => {
      render(<HarmWarning {...defaultProps} harmResult={{ ...defaultProps.harmResult, severity: 'medium' }} />);
      expect(screen.getByText('⚠️')).toBeInTheDocument();
    });
  });
});
