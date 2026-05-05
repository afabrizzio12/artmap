import Image from 'next/image';
import * as React from 'react';

type SearchEntityType = 'museum' | 'artwork' | 'artist';

interface BaseSearchRowProps {
  type: SearchEntityType;
  primary: string;
  secondary?: string;
  onSelect?: () => void;
}

interface MuseumRowProps extends BaseSearchRowProps {
  type: 'museum';
}

interface ArtworkRowProps extends BaseSearchRowProps {
  type: 'artwork';
  thumbnailUrl: string;
}

interface ArtistRowProps extends BaseSearchRowProps {
  type: 'artist';
  portraitUrl?: string;
  /** Initials fallback when no portrait available */
  initials?: string;
}

type SearchRowProps = MuseumRowProps | ArtworkRowProps | ArtistRowProps;

/**
 * SearchRow — three visual variants for the three searchable entity types.
 *
 * Museum: building icon, name, city/country
 * Artwork: 40px square thumbnail, title + artist, medium · institution
 * Artist: 36px circular portrait (or initials), name, era/movement
 *
 * Used inside the search dropdown. Keyboard navigation is handled by the
 * parent listbox — this component only renders.
 */
export function SearchRow(props: SearchRowProps) {
  const baseClasses =
    'w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-left ' +
    'transition-colors duration-100 ' +
    'hover:bg-[var(--color-surface)] ' +
    'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] ' +
    'focus-visible:outline-[var(--color-accent)]';

  return (
    <button
      type="button"
      onClick={props.onSelect}
      className={baseClasses}
      role="option"
      aria-selected="false"
    >
      <RowVisual {...props} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-[var(--color-text-primary)] truncate">
          {props.primary}
        </p>
        {props.secondary && (
          <p className="text-xs text-[var(--color-text-muted)] truncate mt-0.5">
            {props.secondary}
          </p>
        )}
      </div>
    </button>
  );
}

function RowVisual(props: SearchRowProps) {
  if (props.type === 'museum') {
    return (
      <div
        className="flex-shrink-0 w-10 h-10 rounded-md flex items-center justify-center text-[var(--color-text-muted)] bg-[var(--color-surface)]"
        aria-hidden="true"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path
            d="M2 16h14M3 16V8M15 16V8M5 16V10M8 16V10M11 16V10M13 16V10M2 8h14L9 2L2 8Z"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    );
  }

  if (props.type === 'artwork') {
    return (
      <div className="flex-shrink-0 relative w-10 h-10 rounded-sm overflow-hidden bg-[var(--color-surface)]">
        <Image
          src={props.thumbnailUrl}
          alt=""
          fill
          sizes="40px"
          className="object-cover"
          unoptimized
        />
      </div>
    );
  }

  // artist
  if (props.portraitUrl) {
    return (
      <div className="flex-shrink-0 relative w-9 h-9 rounded-full overflow-hidden bg-[var(--color-surface)]">
        <Image
          src={props.portraitUrl}
          alt=""
          fill
          sizes="36px"
          className="object-cover"
          unoptimized
        />
      </div>
    );
  }
  return (
    <div
      className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center bg-[var(--color-accent)] text-[var(--color-bg)] text-xs font-medium"
      aria-hidden="true"
    >
      {props.initials || '·'}
    </div>
  );
}
