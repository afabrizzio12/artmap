import Link from 'next/link';
import * as React from 'react';

interface BackPillProps {
  /** The entity to return to, e.g. "Rodin", "the Louvre", "Italian Renaissance" */
  label: string;
  /** Where back goes */
  href: string;
}

/**
 * BackPill — semantic back navigation. Different from browser back:
 * this returns to a specific previously-viewed detail page.
 *
 * Renders as: ← Back to Rodin
 *
 * Should only be rendered when the user arrived at the current page from
 * another detail page (not from the map or homepage). The parent route
 * is responsible for that logic — this component just renders.
 *
 * Placed above the breadcrumb on detail pages.
 */
export function BackPill({ label, href }: BackPillProps) {
  return (
    <Link
      href={href}
      className={
        'inline-flex items-center gap-1.5 mb-2 px-3 py-1 rounded-pill text-xs ' +
        'bg-[var(--color-surface)] text-[var(--color-text-muted)] ' +
        'hover:bg-[var(--color-border)] hover:text-[var(--color-text-primary)] ' +
        'transition-colors duration-150 ' +
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]'
      }
    >
      <span aria-hidden="true">←</span>
      <span>Back to {label}</span>
    </Link>
  );
}
