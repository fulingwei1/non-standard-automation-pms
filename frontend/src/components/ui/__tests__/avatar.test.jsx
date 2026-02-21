import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock Avatar component
const Avatar = ({ src, alt = 'avatar', fallback, size = 'md', className }) => {
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
    xl: 'w-16 h-16 text-lg',
  };

  return (
    <div className={`avatar ${sizeClasses[size]} ${className || ''}`}>
      {src ? (
        <img src={src} alt={alt} className="avatar-image" />
      ) : (
        <span className="avatar-fallback">{fallback || alt.charAt(0).toUpperCase()}</span>
      )}
    </div>
  );
};

describe('Avatar', () => {
  describe('Basic Rendering', () => {
    it('renders avatar component', () => {
      const { container } = render(<Avatar />);
      expect(container.querySelector('.avatar')).toBeInTheDocument();
    });

    it('renders with image source', () => {
      render(<Avatar src="/user.jpg" alt="用户头像" />);
      const image = screen.getByAltText('用户头像');
      expect(image).toBeInTheDocument();
      expect(image.tagName).toBe('IMG');
    });

    it('renders fallback when no image', () => {
      const { container } = render(<Avatar fallback="AB" />);
      expect(screen.getByText('AB')).toBeInTheDocument();
    });

    it('generates fallback from alt text', () => {
      const { container } = render(<Avatar alt="John Doe" />);
      expect(screen.getByText('J')).toBeInTheDocument();
    });
  });

  describe('Image Handling', () => {
    it('displays image when src is provided', () => {
      render(<Avatar src="https://example.com/avatar.jpg" />);
      const image = screen.getByRole('img');
      expect(image.src).toContain('avatar.jpg');
    });

    it('sets correct alt text', () => {
      render(<Avatar src="/avatar.jpg" alt="用户头像" />);
      const image = screen.getByAltText('用户头像');
      expect(image).toBeInTheDocument();
    });

    it('has default alt text', () => {
      render(<Avatar src="/avatar.jpg" />);
      const image = screen.getByAltText('avatar');
      expect(image).toBeInTheDocument();
    });

    it('applies image className', () => {
      const { container } = render(<Avatar src="/avatar.jpg" />);
      const image = container.querySelector('.avatar-image');
      expect(image).toBeInTheDocument();
    });
  });

  describe('Fallback Text', () => {
    it('displays custom fallback text', () => {
      render(<Avatar fallback="JD" />);
      expect(screen.getByText('JD')).toBeInTheDocument();
    });

    it('displays single character fallback', () => {
      render(<Avatar fallback="A" />);
      expect(screen.getByText('A')).toBeInTheDocument();
    });

    it('displays multi-character fallback', () => {
      render(<Avatar fallback="ABC" />);
      expect(screen.getByText('ABC')).toBeInTheDocument();
    });

    it('capitalizes first letter of alt for fallback', () => {
      render(<Avatar alt="john" />);
      expect(screen.getByText('J')).toBeInTheDocument();
    });

    it('applies fallback className', () => {
      const { container } = render(<Avatar fallback="X" />);
      expect(container.querySelector('.avatar-fallback')).toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    it('renders small size', () => {
      const { container } = render(<Avatar size="sm" />);
      const avatar = container.querySelector('.avatar');
      expect(avatar).toHaveClass('w-8', 'h-8', 'text-xs');
    });

    it('renders medium size (default)', () => {
      const { container } = render(<Avatar size="md" />);
      const avatar = container.querySelector('.avatar');
      expect(avatar).toHaveClass('w-10', 'h-10', 'text-sm');
    });

    it('renders large size', () => {
      const { container } = render(<Avatar size="lg" />);
      const avatar = container.querySelector('.avatar');
      expect(avatar).toHaveClass('w-12', 'h-12', 'text-base');
    });

    it('renders extra large size', () => {
      const { container } = render(<Avatar size="xl" />);
      const avatar = container.querySelector('.avatar');
      expect(avatar).toHaveClass('w-16', 'h-16', 'text-lg');
    });

    it('uses medium size by default', () => {
      const { container } = render(<Avatar />);
      const avatar = container.querySelector('.avatar');
      expect(avatar).toHaveClass('w-10', 'h-10');
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(<Avatar className="custom-avatar" />);
      expect(container.querySelector('.custom-avatar')).toBeInTheDocument();
    });

    it('merges custom className with size classes', () => {
      const { container } = render(
        <Avatar size="lg" className="rounded-full border-2" />
      );
      const avatar = container.querySelector('.avatar');
      expect(avatar).toHaveClass('rounded-full', 'border-2', 'w-12', 'h-12');
    });
  });

  describe('Edge Cases', () => {
    it('handles empty src', () => {
      const { container } = render(<Avatar src="" />);
      expect(container.querySelector('.avatar-fallback')).toBeInTheDocument();
    });

    it('handles undefined src', () => {
      const { container } = render(<Avatar src={undefined} />);
      expect(container.querySelector('.avatar-fallback')).toBeInTheDocument();
    });

    it('handles empty alt text', () => {
      const { container } = render(<Avatar alt="" />);
      expect(container.querySelector('.avatar')).toBeInTheDocument();
    });

    it('handles very long alt text', () => {
      render(<Avatar alt="这是一个非常非常长的名字用于测试" />);
      expect(screen.getByText('这')).toBeInTheDocument();
    });

    it('handles special characters in alt', () => {
      render(<Avatar alt="@user123" />);
      expect(screen.getByText('@')).toBeInTheDocument();
    });

    it('handles numeric alt text', () => {
      render(<Avatar alt="123" />);
      expect(screen.getByText('1')).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot with image', () => {
      const { container } = render(
        <Avatar src="/avatar.jpg" alt="用户" />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with fallback', () => {
      const { container } = render(<Avatar fallback="AB" />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with different sizes', () => {
      ['sm', 'md', 'lg', 'xl'].forEach((size) => {
        const { container } = render(<Avatar size={size} fallback="A" />);
        expect(container).toMatchSnapshot();
      });
    });

    it('matches snapshot with custom styling', () => {
      const { container } = render(
        <Avatar
          src="/avatar.jpg"
          size="lg"
          className="rounded-full shadow-lg"
        />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
