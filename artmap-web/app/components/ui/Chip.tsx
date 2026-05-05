'use client';

import * as React from 'react';

interface ChipProps {
  active?: boolean;
  onClick?: () => void;
  onRemove?: () => void;
  children: React.ReactNode;
}

/**
 * Chip — used for filter chips and active relational lens indicators.
 *
 * Active state shows a × affordance to remove the filter.
 * Inactive state is clickable to apply the filter.
 *
 * Always paired with a "Clear all" link in the parent when any chip is active.
 */
export function Chip({ active = false, onClick, onRemove, children }: ChipProps) {
  const baseStyles =
    'inline-flex items-center gap-2 h-8 px-4 rounded-pill text-sm ' +
    'transition-colors duration-150 ' +
    'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ' +
    'focus-visible:outline-[var(--color-accent)]';

  if (active) {
    return (
      <span
        className={
          baseStyles +
          ' bg-[var(--color-chip-active-bg)] text-[var(--color-chip-active-text)] font-medium'
        }
      >
        {children}
        {onRemove && (
          <button
            type="button"
            onClick={onRemove}
            aria-label="Remove filter"
            className="ml-1 -mr-1 inline-flex items-center justify-center w-4 h-4 rounded-full hover:bg-[var(--color-accent-hover)]"
          >
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
              <path
                d="M1.5 1.5L8.5 8.5M8.5 1.5L1.5 8.5"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </button>
        )}
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={
        baseStyles +
        ' bg-[var(--color-chip-inactive-bg)] text-[var(--color-text-primary)] ' +
        'border border-[var(--color-chip-inactive-border)] ' +
        'hover:border-[var(--color-text-muted)]'
      }
    >
      {children}
    </button>
  );
}
