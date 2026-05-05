import * as React from 'react';

interface MapPinProps {
  /** When provided, renders as a cluster with the count inside */
  count?: number;
  /** Visual size — cluster size scales with count */
  size?: 'sm' | 'md' | 'lg';
  /** When true, indicates a "related work" pin distinct from a "primary" pin */
  related?: boolean;
}

/**
 * MapPin — visual specification for map pins and clusters.
 *
 * Single pins are 16px circles in steel blue with a 2.5px cream stroke.
 * Cluster circles scale with density (20/28/36px) and contain a count.
 *
 * "Related" pins (used on the artwork mini-map for "related works in the
 * same city") are rendered with a hollow center to visually distinguish
 * them from "primary" pins. This is critical: the user must understand
 * at a glance that related works are not works by the same artist.
 *
 * This component is for design-system rendering and the /design-system
 * reference page. The actual map uses MapLibre layer styles which read
 * from the same color tokens (defined in globals.css).
 */
export function MapPin({ count, size = 'md', related = false }: MapPinProps) {
  if (count !== undefined) {
    const dimensions = { sm: 20, md: 28, lg: 36 }[size];
    return (
      <span
        className="inline-flex items-center justify-center rounded-full bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold tabular"
        style={{
          width: dimensions,
          height: dimensions,
          fontSize: size === 'sm' ? 10 : size === 'md' ? 12 : 13,
          boxShadow: '0 0 0 2.5px var(--color-bg)',
        }}
      >
        {count}
      </span>
    );
  }

  if (related) {
    return (
      <span
        className="inline-block rounded-full"
        style={{
          width: 16,
          height: 16,
          background: 'var(--color-bg)',
          border: '2.5px solid var(--color-accent)',
          boxShadow: '0 0 0 1.5px var(--color-bg)',
        }}
      />
    );
  }

  return (
    <span
      className="inline-block rounded-full bg-[var(--color-accent)]"
      style={{
        width: 16,
        height: 16,
        boxShadow: '0 0 0 2.5px var(--color-bg)',
      }}
    />
  );
}
