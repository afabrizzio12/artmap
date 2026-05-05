import * as React from 'react';

/**
 * Relationship marks — the five iconographic marks paired with relationship
 * card labels. Drawn as bookplate-style line illustrations rather than UI
 * icons. Always rendered at 12px next to their label, in smoke taupe.
 *
 * Never use pale gold for these marks. The marks are connective tissue,
 * not chromatic events.
 */

type MarkSize = 12 | 16 | 24;

interface MarkProps {
  size?: MarkSize;
  className?: string;
}

const sharedProps = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

/** Lineage — chain link, suggesting transmission */
export function LineageMark({ size = 12, className = '' }: MarkProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" className={className} {...sharedProps}>
      <ellipse cx="4" cy="6" rx="2" ry="2.5" />
      <ellipse cx="8" cy="6" rx="2" ry="2.5" />
    </svg>
  );
}

/** Dialogue — two opposing arrows */
export function DialogueMark({ size = 12, className = '' }: MarkProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" className={className} {...sharedProps}>
      <path d="M2 4.5 L8.5 4.5 M6 2.5 L8.5 4.5 L6 6.5" />
      <path d="M10 7.5 L3.5 7.5 M6 5.5 L3.5 7.5 L6 9.5" />
    </svg>
  );
}

/** Co-presence — single dot */
export function CoPresenceMark({ size = 12, className = '' }: MarkProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" className={className} {...sharedProps}>
      <circle cx="6" cy="6" r="2" fill="currentColor" />
    </svg>
  );
}

/** Movement — three connected dots */
export function MovementMark({ size = 12, className = '' }: MarkProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" className={className} {...sharedProps}>
      <circle cx="2.5" cy="6" r="1" fill="currentColor" />
      <circle cx="6" cy="6" r="1" fill="currentColor" />
      <circle cx="9.5" cy="6" r="1" fill="currentColor" />
      <line x1="3.5" y1="6" x2="5" y2="6" />
      <line x1="7" y1="6" x2="8.5" y2="6" />
    </svg>
  );
}

/** Reinterpretation — mirror shape, suggesting reflection or remix */
export function ReinterpretationMark({ size = 12, className = '' }: MarkProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" className={className} {...sharedProps}>
      <path d="M6 2 L3 6 L6 10" />
      <path d="M6 2 L9 6 L6 10" />
      <line x1="6" y1="2" x2="6" y2="10" strokeDasharray="1 1.5" />
    </svg>
  );
}

export type RelationshipType =
  | 'lineage'
  | 'dialogue'
  | 'co-presence'
  | 'movement'
  | 'reinterpretation';

const markComponents: Record<RelationshipType, React.FC<MarkProps>> = {
  lineage: LineageMark,
  dialogue: DialogueMark,
  'co-presence': CoPresenceMark,
  movement: MovementMark,
  reinterpretation: ReinterpretationMark,
};

interface RelationshipMarkProps extends MarkProps {
  type: RelationshipType;
}

/** Convenience — pick the mark by relationship type */
export function RelationshipMark({ type, ...props }: RelationshipMarkProps) {
  const Component = markComponents[type];
  return <Component {...props} />;
}
