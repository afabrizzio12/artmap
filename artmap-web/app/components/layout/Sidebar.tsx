'use client';

import Link from 'next/link';
import * as React from 'react';
import { usePathname } from 'next/navigation';

interface SidebarProps {
  /** When true, sidebar is 240px expanded. When false, 64px collapsed. */
  expanded: boolean;
  /** Callback fired when the user toggles the chevron */
  onToggle?: () => void;
  /**
   * Optional context content rendered in the lower portion of the sidebar
   * when expanded. Used to host the persistent mini-map widget on detail
   * pages, or contextual entity info.
   */
  context?: React.ReactNode;
}

interface NavItemProps {
  href: string;
  label: string;
  icon: React.ReactNode;
  expanded: boolean;
  active: boolean;
}

function NavItem({ href, label, icon, expanded, active }: NavItemProps) {
  return (
    <Link
      href={href}
      aria-current={active ? 'page' : undefined}
      className={
        'flex items-center gap-3 h-11 rounded-md transition-colors duration-150 ' +
        (expanded ? 'px-3' : 'px-0 justify-center') +
        ' ' +
        (active
          ? 'bg-[var(--color-surface)] text-[var(--color-accent)]'
          : 'text-[var(--color-text-primary)] hover:bg-[var(--color-surface)]') +
        ' focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]'
      }
    >
      <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center" aria-hidden="true">
        {icon}
      </span>
      {expanded && <span className="text-sm font-medium">{label}</span>}
    </Link>
  );
}

/**
 * Sidebar — the global left navigation shell.
 *
 * Two states: collapsed (64px) and expanded (240px). Collapsed is the
 * default on the map screen; expanded is the default on all detail pages.
 *
 * The lower portion (when expanded) hosts the persistent mini-map widget
 * via the `context` prop on detail pages.
 */
export function Sidebar({ expanded, onToggle, context }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={
        'flex-shrink-0 h-full flex flex-col bg-[var(--color-bg)] ' +
        'border-r border-[var(--color-border)] ' +
        'transition-[width] duration-200 ease-out ' +
        (expanded ? 'w-60' : 'w-16')
      }
      aria-label="Primary navigation"
    >
      {/* Logo / wordmark */}
      <div className={'h-16 flex items-center ' + (expanded ? 'px-4' : 'justify-center')}>
        <Link
          href="/"
          className="font-semibold text-lg text-[var(--color-text-primary)] hover:text-[var(--color-accent)] transition-colors"
        >
          {expanded ? 'ArtMap' : 'A'}
        </Link>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-2 py-2 flex flex-col gap-1">
        <NavItem
          href="/map"
          label="Map"
          expanded={expanded}
          active={pathname === '/map' || pathname?.startsWith('/map/')}
          icon={<MapIcon />}
        />
        <NavItem
          href="/search"
          label="Search"
          expanded={expanded}
          active={pathname?.startsWith('/search') ?? false}
          icon={<SearchIcon />}
        />
        <NavItem
          href="/collections"
          label="Collections"
          expanded={expanded}
          active={pathname?.startsWith('/collections') ?? false}
          icon={<BookmarkIcon />}
        />
      </nav>

      {/* Contextual content (e.g., mini-map widget on detail pages) */}
      {expanded && context && (
        <div className="px-2 py-3 border-t border-[var(--color-border)]">
          {context}
        </div>
      )}

      {/* Bottom: account placeholder + toggle */}
      <div
        className={
          'flex items-center gap-2 p-3 border-t border-[var(--color-border)] ' +
          (expanded ? 'justify-between' : 'flex-col')
        }
      >
        <div
          className="w-8 h-8 rounded-full bg-[var(--color-surface)] flex items-center justify-center text-xs text-[var(--color-text-muted)]"
          aria-label="Account"
        >
          A
        </div>
        {onToggle && (
          <button
            type="button"
            onClick={onToggle}
            aria-label={expanded ? 'Collapse sidebar' : 'Expand sidebar'}
            className="w-8 h-8 rounded-md flex items-center justify-center text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path
                d={expanded ? 'M9 3.5L5.5 7L9 10.5' : 'M5 3.5L8.5 7L5 10.5'}
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        )}
      </div>
    </aside>
  );
}

function MapIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path
        d="M9 16C9 16 14 11 14 7C14 4.24 11.76 2 9 2C6.24 2 4 4.24 4 7C4 11 9 16 9 16Z"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinejoin="round"
      />
      <circle cx="9" cy="7" r="1.8" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <circle cx="8" cy="8" r="5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M11.5 11.5L15 15" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

function BookmarkIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path
        d="M4 2H14V16L9 12L4 16V2Z"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinejoin="round"
      />
    </svg>
  );
}
