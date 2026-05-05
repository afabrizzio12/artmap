import Image from 'next/image';
import Link from 'next/link';
import * as React from 'react';

interface PolaroidCardProps {
  /** The artwork's image URL. If null/undefined, the card is not rendered. */
  imageUrl: string | null | undefined;
  /** Alt text for the image. Required for accessibility. */
  imageAlt: string;
  /** Primary text — typically the artwork title. */
  title: string;
  /** Secondary text — typically the artist name. */
  subtitle?: string;
  /** Optional href — if provided, the card is wrapped in a Next.js Link. */
  href?: string;
  /** Optional badge — rendered in pale gold uppercase, e.g. "Original work". */
  badge?: string;
  /** Width of the card. Defaults to 160px (the standard atom size). */
  width?: number;
}

/**
 * PolaroidCard — the visual atom of ArtMap.
 *
 * Image on top (3:4 aspect ratio), title and subtitle below. Used inside
 * relationship cards, carousels, search results, and museum/period grids.
 *
 * Hard rule: if imageUrl is missing, the card returns null — never render
 * an empty placeholder. ArtMap loses meaning without images, and the
 * data layer is responsible for ensuring every surfaced entity has one.
 */
export function PolaroidCard({
  imageUrl,
  imageAlt,
  title,
  subtitle,
  href,
  badge,
  width = 160,
}: PolaroidCardProps) {
  if (!imageUrl) return null;

  const inner = (
    <article
      className={
        'group flex flex-col rounded-md overflow-hidden ' +
        'bg-[var(--color-bg)] border border-[var(--color-border)] ' +
        'transition-all duration-150 ' +
        'hover:border-[var(--color-chip-inactive-border)] hover:-translate-y-0.5'
      }
      style={{ width }}
    >
      <div
        className="relative w-full bg-[var(--color-surface)]"
        style={{ aspectRatio: '3 / 4' }}
      >
        <Image
          src={imageUrl}
          alt={imageAlt}
          fill
          sizes={`${width}px`}
          className="object-cover"
          unoptimized
        />
        {badge && (
          <span
            className={
              'absolute top-2 left-2 px-2 py-0.5 rounded-sm ' +
              'bg-[var(--color-bg)]/90 text-[var(--color-callout)] ' +
              'text-xs font-medium uppercase tracking-wider'
            }
          >
            {badge}
          </span>
        )}
      </div>
      <div className="px-3 py-2.5">
        <p className="text-sm font-semibold text-[var(--color-text-primary)] line-clamp-2 leading-snug">
          {title}
        </p>
        {subtitle && (
          <p className="text-xs text-[var(--color-text-muted)] mt-0.5 line-clamp-1">
            {subtitle}
          </p>
        )}
      </div>
    </article>
  );

  if (href) {
    return (
      <Link href={href} className="block focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)] rounded-md">
        {inner}
      </Link>
    );
  }

  return inner;
}
