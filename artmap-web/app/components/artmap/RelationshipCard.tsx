import * as React from 'react';
import {
  RelationshipMark,
  type RelationshipType,
} from './RelationshipMarks';

interface RelationshipCardProps {
  /** Which of the five relationship types this card represents */
  type: RelationshipType;
  /** Section title in pewter ink, e.g. "Raphael learned from Da Vinci" */
  title: string;
  /** Optional CTA label — e.g. "View all 23 works" */
  ctaLabel?: string;
  /** CTA link target */
  ctaHref?: string;
  /** Polaroid cards to render in the horizontal row */
  children: React.ReactNode;
}

const labelMap: Record<RelationshipType, string> = {
  lineage: 'Lineage',
  dialogue: 'Dialogue',
  'co-presence': 'Co-presence',
  movement: 'Movement',
  reinterpretation: 'Reinterpretation',
};

/**
 * RelationshipCard — the structural component for surfacing relationships
 * between entities. Five variants share a single skeleton; only the label
 * text and the iconographic mark change. No color differentiation.
 *
 * Usage:
 *
 *   <RelationshipCard
 *     type="lineage"
 *     title="Raphael learned from Da Vinci"
 *     ctaLabel="View all"
 *     ctaHref="/lineage/da-vinci"
 *   >
 *     <PolaroidCard ... />
 *     <PolaroidCard ... />
 *   </RelationshipCard>
 */
export function RelationshipCard({
  type,
  title,
  ctaLabel,
  ctaHref,
  children,
}: RelationshipCardProps) {
  return (
    <section className="py-6">
      {/* Label row: mark + uppercase label */}
      <div className="flex items-center gap-2 mb-2 text-[var(--color-text-muted)]">
        <RelationshipMark type={type} size={12} />
        <span className="label-meta">{labelMap[type]}</span>
      </div>

      {/* Section title */}
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
        {title}
      </h3>

      {/* Horizontal scroll row of polaroid cards */}
      <div className="flex gap-3 overflow-x-auto pb-2 -mx-2 px-2 scroll-smooth">
        {children}
      </div>

      {/* Optional CTA */}
      {ctaLabel && ctaHref && (
        <a
          href={ctaHref}
          className="inline-flex items-center gap-1 mt-4 text-sm font-medium text-[var(--color-accent)] hover:text-[var(--color-accent-hover)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)] rounded"
        >
          {ctaLabel}
          <span aria-hidden="true">→</span>
        </a>
      )}
    </section>
  );
}
