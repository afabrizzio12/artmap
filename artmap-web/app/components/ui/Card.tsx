import * as React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Use 'default' for primary content surfaces.
   * Use 'subtle' for secondary surfaces inside a section
   * (e.g., the count callout block on a museum page).
   */
  variant?: 'default' | 'subtle';
  children: React.ReactNode;
}

/**
 * Card — a generic surface container with cream background and 0.5px border.
 *
 * Most ArtMap "card-like" things (PolaroidCard, RelationshipCard) do not
 * use this primitive — they have their own specialized markup. This Card
 * is for ad-hoc content blocks that need surface treatment.
 */
export function Card({
  variant = 'default',
  className = '',
  children,
  ...props
}: CardProps) {
  const variantStyles = {
    default:
      'bg-[var(--color-bg)] border border-[var(--color-border)]',
    subtle:
      'bg-[var(--color-surface)] border border-transparent',
  };

  return (
    <div
      className={[
        'rounded-lg p-5',
        variantStyles[variant],
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...props}
    >
      {children}
    </div>
  );
}
