import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import GhostText from '../../components/GhostText';

describe('GhostText Component', () => {
  const defaultProps = {
    text: 'eckout main',
    position: { x: 100, y: 200 },
    fontSize: 14,
  };

  // ============ Rendering Tests ============

  describe('Rendering', () => {
    it('renders ghost text when text is provided', () => {
      render(<GhostText {...defaultProps} />);
      expect(screen.getByText('eckout main')).toBeInTheDocument();
    });

    it('does not render when text is empty', () => {
      const { container } = render(<GhostText {...defaultProps} text="" />);
      expect(container.firstChild).toBeNull();
    });

    it('does not render when text is null/undefined', () => {
      const { container } = render(<GhostText {...defaultProps} text={undefined as any} />);
      expect(container.firstChild).toBeNull();
    });
  });

  // ============ Positioning Tests ============

  describe('Positioning', () => {
    it('positions at correct coordinates', () => {
      render(<GhostText {...defaultProps} />);
      const element = screen.getByText('eckout main');
      
      expect(element).toHaveStyle({ left: '100px' });
      expect(element).toHaveStyle({ top: '200px' });
    });

    it('uses correct font size', () => {
      render(<GhostText {...defaultProps} fontSize={16} />);
      const element = screen.getByText('eckout main');
      
      expect(element).toHaveStyle({ fontSize: '16px' });
    });

    it('handles different positions', () => {
      render(<GhostText {...defaultProps} position={{ x: 50, y: 75 }} />);
      const element = screen.getByText('eckout main');
      
      expect(element).toHaveStyle({ left: '50px' });
      expect(element).toHaveStyle({ top: '75px' });
    });
  });

  // ============ Explanation Tooltip Tests ============

  describe('Explanation Tooltip', () => {
    it('shows info icon when explanation is provided', () => {
      render(<GhostText {...defaultProps} explanation="Switch to main branch" />);
      expect(screen.getByText('ⓘ')).toBeInTheDocument();
    });

    it('does not show info icon when no explanation', () => {
      render(<GhostText {...defaultProps} />);
      expect(screen.queryByText('ⓘ')).not.toBeInTheDocument();
    });

    it('shows tooltip on mouse enter', () => {
      render(<GhostText {...defaultProps} explanation="Switch to main branch" />);
      const element = screen.getByText('eckout main').parentElement!;
      
      fireEvent.mouseEnter(element);
      
      expect(screen.getByText('Switch to main branch')).toBeInTheDocument();
    });

    it('hides tooltip on mouse leave', () => {
      render(<GhostText {...defaultProps} explanation="Switch to main branch" />);
      const element = screen.getByText('eckout main').parentElement!;
      
      fireEvent.mouseEnter(element);
      expect(screen.getByText('Switch to main branch')).toBeInTheDocument();
      
      fireEvent.mouseLeave(element);
      expect(screen.queryByText('Switch to main branch')).not.toBeInTheDocument();
    });
  });

  // ============ Style Tests ============

  describe('Styling', () => {
    it('has italic font style', () => {
      render(<GhostText {...defaultProps} />);
      const element = screen.getByText('eckout main');
      
      expect(element).toHaveStyle({ fontStyle: 'italic' });
    });

    it('has fixed positioning', () => {
      render(<GhostText {...defaultProps} />);
      const element = screen.getByText('eckout main');
      
      expect(element).toHaveStyle({ position: 'fixed' });
    });

    it('uses monospace font family', () => {
      render(<GhostText {...defaultProps} />);
      const element = screen.getByText('eckout main');
      
      expect(element.style.fontFamily).toContain('Consolas');
    });
  });

  // ============ Memoization Tests ============

  describe('Memoization', () => {
    it('is memoized component', () => {
      const { rerender } = render(<GhostText {...defaultProps} />);
      const firstElement = screen.getByText('eckout main');
      
      // Re-render with same props
      rerender(<GhostText {...defaultProps} />);
      const secondElement = screen.getByText('eckout main');
      
      // Elements should be the same (memoized)
      expect(firstElement).toBe(secondElement);
    });
  });
});
