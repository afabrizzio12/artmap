import * as React from 'react';

type ButtonVariant = 'primary' | 'outline' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
}

const baseStyles =
  'inline-flex items-center justify-center gap-2 font-medium rounded-md ' +
  'transition-colors duration-150 ' +
  'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ' +
  'focus-visible:outline-[var(--color-accent)] ' +
  'disabled:opacity-50 disabled:cursor-not-allowed';

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-[var(--color-accent)] text-[var(--color-bg)] ' +
    'hover:bg-[var(--color-accent-hover)]',
  outline:
    'bg-transparent text-[var(--color-accent)] ' +
    'border border-[var(--color-accent)] ' +
    'hover:bg-[var(--color-accent)] hover:text-[var(--color-bg)]',
  ghost:
    'bg-transparent text-[var(--color-text-primary)] ' +
    'hover:bg-[var(--color-surface)]',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-11 px-4 text-sm',
  lg: 'h-12 px-5 text-base',
};

/**
 * Button — primary, outline, ghost variants.
 *
 * Use primary for the canonical CTA on a page.
 * Use outline for "Add to Collection"-style secondary CTAs.
 * Use ghost for inline / low-emphasis actions inside lists or cards.
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      className = '',
      children,
      ...props
    },
    ref,
  ) {
    return (
      <button
        ref={ref}
        className={[
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          fullWidth ? 'w-full' : '',
          className,
        ]
          .filter(Boolean)
          .join(' ')}
        {...props}
      >
        {children}
      </button>
    );
  },
);
