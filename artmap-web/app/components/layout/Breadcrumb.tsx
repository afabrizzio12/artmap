import Link from 'next/link';
import * as React from 'react';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

/**
 * Breadcrumb — part of the anti-disorientation system.
 *
 * Format: Map › Louvre › Italian Renaissance › Mona Lisa
 * The final item (current page) is not a link; all others are.
 *
 * Always rendered above the page title on detail pages. Invisible
 * navigation when not needed; lifeline when it is.
 */
export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className="mb-3">
      <ol className="flex items-center gap-1.5 flex-wrap text-xs text-[var(--color-text-muted)]">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li key={index} className="flex items-center gap-1.5">
              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  className="hover:text-[var(--color-accent)] transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)] rounded"
                >
                  {item.label}
                </Link>
              ) : (
                <span className={isLast ? 'text-[var(--color-text-primary)]' : ''}>
                  {item.label}
                </span>
              )}
              {!isLast && <span aria-hidden="true">›</span>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
