import * as React from 'react';
import { Button } from '@/app/components/ui/Button';
import { Chip } from '@/app/components/ui/Chip';
import { Card } from '@/app/components/ui/Card';
import { PolaroidCard } from '@/app/components/artmap/PolaroidCard';
import { RelationshipCard } from '@/app/components/artmap/RelationshipCard';
import {
  LineageMark,
  DialogueMark,
  CoPresenceMark,
  MovementMark,
  ReinterpretationMark,
} from '@/app/components/artmap/RelationshipMarks';
import { SearchRow } from '@/app/components/artmap/SearchRow';
import { MapPin } from '@/app/components/artmap/MapPin';
import { Breadcrumb } from '@/app/components/layout/Breadcrumb';
import { BackPill } from '@/app/components/layout/BackPill';

export const metadata = {
  title: 'Design system',
  description: 'The ArtMap design system reference. Tokens, components, patterns.',
};

// ---------- Sample images (Met Museum CC0 — your primary data source) ----------
const STARRY_NIGHT =
  'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/640px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg';
const MONA_LISA =
  'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/480px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg';
const VENUS_DE_MILO =
  'https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Front_views_of_the_Venus_de_Milo.jpg/360px-Front_views_of_the_Venus_de_Milo.jpg';
const THE_THINKER =
  'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/The_Thinker_close.jpg/360px-The_Thinker_close.jpg';
const SCHOOL_OF_ATHENS =
  'https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Sanzio_01.jpg/640px-Sanzio_01.jpg';

export default function DesignSystemPage() {
  return (
    <main className="min-h-screen bg-[var(--color-bg)]">
      <div className="max-w-5xl mx-auto px-6 py-12">
        <header className="mb-12 pb-8 border-b border-[var(--color-border)]">
          <p className="label-meta mb-2">Design system · v1</p>
          <h1 className="text-4xl font-semibold text-[var(--color-text-primary)]">
            ArtMap
          </h1>
          <p className="text-base text-[var(--color-text-muted)] mt-3 max-w-2xl">
            The visual reference for every component, token, and pattern in ArtMap.
            Use this page when implementing screens or designing in Figma — what
            you see here is what gets shipped.
          </p>
        </header>

        <Section
          number="1"
          title="Foundations"
          description="Color, typography, spacing, and radii."
        />
        <Foundations />

        <Section
          number="2"
          title="Atoms"
          description="The smallest interactive elements: buttons, chips, navigation primitives."
        />
        <Atoms />

        <Section
          number="3"
          title="Polaroid card"
          description="The visual atom of ArtMap. Image-on-top, title and subtitle below. Used everywhere artworks appear."
        />
        <PolaroidShowcase />

        <Section
          number="4"
          title="Relationship cards"
          description="Five variants for the five relationship types. Same skeleton, different label and mark. No color differentiation between variants."
        />
        <RelationshipShowcase />

        <Section
          number="5"
          title="Search rows"
          description="Three variants for the three searchable entity types."
        />
        <SearchRowShowcase />

        <Section
          number="6"
          title="Map pins & clusters"
          description="The visual specification for map pins. The actual map uses MapLibre styles that read from the same color tokens."
        />
        <MapPinShowcase />

        <Section
          number="7"
          title="Patterns"
          description="The three rules every detail page must implement."
        />
        <Patterns />
      </div>
    </main>
  );
}

// ============================================================================
// Section header
// ============================================================================

function Section({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="mt-16 mb-8">
      <p className="label-meta mb-1">Section {number}</p>
      <h2 className="text-2xl font-semibold text-[var(--color-text-primary)]">
        {title}
      </h2>
      <p className="text-base text-[var(--color-text-muted)] mt-2 max-w-2xl">
        {description}
      </p>
    </div>
  );
}

// ============================================================================
// 1. Foundations
// ============================================================================

const colorTokens = [
  { name: 'bg', value: '#FBF8F2', usage: 'Page background' },
  { name: 'surface', value: '#F4EDE0', usage: 'Subtle surface differentiation' },
  { name: 'text-primary', value: '#3A4A5C', usage: 'All primary text' },
  { name: 'text-muted', value: '#8B7D6B', usage: 'Metadata, secondary labels' },
  { name: 'accent', value: '#4A6582', usage: 'CTAs, links, pins, active states' },
  { name: 'accent-hover', value: '#3A526B', usage: 'Accent hover, pressed' },
  { name: 'callout', value: '#B8975C', usage: 'Count callouts ONLY' },
  { name: 'border', value: '#E5DFD3', usage: 'Dividers, card borders' },
  { name: 'error', value: '#8B3A3A', usage: 'Errors, destructive actions' },
];

const typeScale = [
  { name: 'Page title (large)', size: 56, weight: 600, sample: 'Mona Lisa' },
  { name: 'Page title', size: 40, weight: 600, sample: 'Musée du Louvre' },
  { name: 'Section header', size: 24, weight: 600, sample: 'About' },
  { name: 'Subsection', size: 18, weight: 600, sample: 'Notable works' },
  { name: 'Body', size: 16, weight: 400, sample: 'The Louvre is the world\'s largest art museum, located on the Right Bank of the Seine.' },
  { name: 'Polaroid title', size: 14, weight: 600, sample: 'Starry Night' },
  { name: 'Small / metadata', size: 13, weight: 400, sample: 'Oil on canvas · 73.7 × 92.1 cm' },
  { name: 'Label (uppercase)', size: 11, weight: 400, sample: 'PARIS, FRANCE', tracking: '0.08em', upper: true },
];

function Foundations() {
  return (
    <div className="space-y-10">
      {/* Colors */}
      <div>
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">Color tokens</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {colorTokens.map((token) => (
            <div
              key={token.name}
              className="border border-[var(--color-border)] rounded-md overflow-hidden"
            >
              <div
                style={{ background: token.value, height: 64 }}
                className="border-b border-[var(--color-border)]"
              />
              <div className="p-3 bg-[var(--color-bg)]">
                <p className="text-sm font-semibold text-[var(--color-text-primary)]">
                  --color-{token.name}
                </p>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5 font-mono">
                  {token.value}
                </p>
                <p className="text-xs text-[var(--color-text-muted)] mt-1.5">{token.usage}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Type scale */}
      <div>
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">Type scale</h3>
        <Card variant="default" className="!p-0">
          <ul className="divide-y divide-[var(--color-border)]">
            {typeScale.map((entry) => (
              <li key={entry.name} className="px-5 py-4 flex items-baseline gap-6">
                <div className="w-40 flex-shrink-0">
                  <p className="text-sm font-semibold text-[var(--color-text-primary)]">
                    {entry.name}
                  </p>
                  <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                    {entry.size}px · {entry.weight}
                  </p>
                </div>
                <p
                  className="text-[var(--color-text-primary)] truncate"
                  style={{
                    fontSize: entry.size,
                    fontWeight: entry.weight,
                    letterSpacing: entry.tracking,
                    textTransform: entry.upper ? 'uppercase' : 'none',
                    color: entry.upper ? 'var(--color-text-muted)' : undefined,
                    lineHeight: 1.1,
                  }}
                >
                  {entry.sample}
                </p>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {/* Count callout demo — the rare moment of warmth */}
      <div>
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
          Count callout
        </h3>
        <p className="text-sm text-[var(--color-text-muted)] mb-3 max-w-xl">
          The only place pale gold appears. Used for collection counts,
          relationship counts, and other data highlights. Never timid — these
          are the chromatic events of the interface.
        </p>
        <Card variant="default" className="max-w-sm">
          <p className="label-meta">Collection</p>
          <p
            className="tabular text-[var(--color-callout)] mt-1"
            style={{ fontSize: 44, fontWeight: 600, lineHeight: 1 }}
          >
            35,000
          </p>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">artworks indexed</p>
        </Card>
      </div>
    </div>
  );
}

// ============================================================================
// 2. Atoms
// ============================================================================

function Atoms() {
  return (
    <div className="space-y-10">
      <ShowcaseRow title="Buttons">
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="primary">Explore museum</Button>
          <Button variant="primary" disabled>Disabled</Button>
          <Button variant="outline">+ Add to Collection</Button>
          <Button variant="ghost">Cancel</Button>
        </div>
      </ShowcaseRow>

      <ShowcaseRow title="Filter chips">
        <div className="flex flex-wrap items-center gap-2">
          <Chip>Era</Chip>
          <Chip>Artist</Chip>
          <Chip>Style</Chip>
          <Chip>Medium</Chip>
          <Chip active onRemove={() => {}}>
            Renaissance
          </Chip>
        </div>
      </ShowcaseRow>

      <ShowcaseRow title="Breadcrumb">
        <Breadcrumb
          items={[
            { label: 'Map', href: '/map' },
            { label: 'Louvre', href: '/museums/louvre' },
            { label: 'Italian Renaissance', href: '/museums/louvre/periods/italian-renaissance' },
            { label: 'Mona Lisa' },
          ]}
        />
      </ShowcaseRow>

      <ShowcaseRow title="Back-pill">
        <BackPill label="Rodin" href="/artists/rodin" />
      </ShowcaseRow>
    </div>
  );
}

function ShowcaseRow({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">{title}</h3>
      <div className="bg-[var(--color-surface)] rounded-lg p-6 border border-[var(--color-border)]">
        {children}
      </div>
    </div>
  );
}

// ============================================================================
// 3. Polaroid card showcase
// ============================================================================

function PolaroidShowcase() {
  return (
    <div className="space-y-6">
      <div className="bg-[var(--color-surface)] rounded-lg p-6 border border-[var(--color-border)]">
        <p className="label-meta mb-4">Default · 160px</p>
        <div className="flex flex-wrap gap-3">
          <PolaroidCard
            imageUrl={STARRY_NIGHT}
            imageAlt="Starry Night by Vincent van Gogh"
            title="Starry Night"
            subtitle="Vincent van Gogh"
          />
          <PolaroidCard
            imageUrl={MONA_LISA}
            imageAlt="Mona Lisa by Leonardo da Vinci"
            title="Mona Lisa"
            subtitle="Leonardo da Vinci"
            badge="Original"
          />
          <PolaroidCard
            imageUrl={VENUS_DE_MILO}
            imageAlt="Venus de Milo"
            title="Venus de Milo"
            subtitle="Unknown · c. 130–100 BCE"
          />
          <PolaroidCard
            imageUrl={THE_THINKER}
            imageAlt="The Thinker by Auguste Rodin"
            title="The Thinker"
            subtitle="Auguste Rodin"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <Card variant="subtle">
          <p className="label-meta mb-2">Hard rule</p>
          <p className="text-[var(--color-text-primary)]">
            If the image URL is missing, the card returns <code>null</code> —
            never an empty placeholder. ArtMap loses meaning without images.
          </p>
        </Card>
        <Card variant="subtle">
          <p className="label-meta mb-2">Hover</p>
          <p className="text-[var(--color-text-primary)]">
            Border darkens to <code>#C4BBA8</code> and the card rises 2px.
            No scale, no color shift, no shadow.
          </p>
        </Card>
      </div>
    </div>
  );
}

// ============================================================================
// 4. Relationship cards
// ============================================================================

function RelationshipShowcase() {
  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
          The five marks
        </h3>
        <div className="bg-[var(--color-surface)] rounded-lg p-6 border border-[var(--color-border)]">
          <div className="grid grid-cols-5 gap-4 text-center text-[var(--color-text-muted)]">
            <MarkShowcase label="Lineage" mark={<LineageMark size={24} />} />
            <MarkShowcase label="Dialogue" mark={<DialogueMark size={24} />} />
            <MarkShowcase label="Co-presence" mark={<CoPresenceMark size={24} />} />
            <MarkShowcase label="Movement" mark={<MovementMark size={24} />} />
            <MarkShowcase label="Reinterpretation" mark={<ReinterpretationMark size={24} />} />
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
          Card example — Lineage
        </h3>
        <div className="bg-[var(--color-bg)] rounded-lg p-6 border border-[var(--color-border)]">
          <RelationshipCard
            type="lineage"
            title="Raphael learned from Da Vinci"
            ctaLabel="View all"
            ctaHref="#"
          >
            <PolaroidCard
              imageUrl={SCHOOL_OF_ATHENS}
              imageAlt="School of Athens by Raphael"
              title="School of Athens"
              subtitle="Raphael"
            />
            <PolaroidCard
              imageUrl={MONA_LISA}
              imageAlt="Mona Lisa"
              title="Mona Lisa"
              subtitle="Leonardo da Vinci"
            />
            <PolaroidCard
              imageUrl={VENUS_DE_MILO}
              imageAlt="Venus de Milo"
              title="Venus de Milo"
              subtitle="Hellenistic"
            />
          </RelationshipCard>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
          Card example — Reinterpretation
        </h3>
        <div className="bg-[var(--color-bg)] rounded-lg p-6 border border-[var(--color-border)]">
          <RelationshipCard
            type="reinterpretation"
            title="The Mona Lisa across the centuries"
            ctaLabel="View all reinterpretations"
            ctaHref="#"
          >
            <PolaroidCard
              imageUrl={MONA_LISA}
              imageAlt="Original Mona Lisa"
              title="Mona Lisa"
              subtitle="Leonardo da Vinci · 1503"
              badge="Original"
            />
            <PolaroidCard
              imageUrl={STARRY_NIGHT}
              imageAlt="Botero Mona Lisa"
              title="Mona Lisa"
              subtitle="Fernando Botero · 1959"
            />
            <PolaroidCard
              imageUrl={THE_THINKER}
              imageAlt="L.H.O.O.Q."
              title="L.H.O.O.Q."
              subtitle="Marcel Duchamp · 1919"
            />
          </RelationshipCard>
        </div>
      </div>
    </div>
  );
}

function MarkShowcase({ label, mark }: { label: string; mark: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="text-[var(--color-text-muted)]">{mark}</div>
      <p className="text-xs text-[var(--color-text-primary)] font-medium">{label}</p>
    </div>
  );
}

// ============================================================================
// 5. Search rows
// ============================================================================

function SearchRowShowcase() {
  return (
    <div className="bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)] overflow-hidden">
      <div className="p-3 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
        <input
          type="text"
          placeholder="Search artworks, artists, museums…"
          className="w-full h-10 px-3 rounded-md bg-[var(--color-bg)] border border-[var(--color-border)] text-sm focus:outline focus:outline-2 focus:outline-[var(--color-accent)]"
          defaultValue="Mona"
        />
      </div>
      <div className="p-2">
        <p className="label-meta px-3 pt-2 pb-1">Museums</p>
        <SearchRow type="museum" primary="Musée du Louvre" secondary="Paris, France" />
        <p className="label-meta px-3 pt-3 pb-1">Artworks</p>
        <SearchRow
          type="artwork"
          thumbnailUrl={MONA_LISA}
          primary="Mona Lisa"
          secondary="Leonardo da Vinci · Oil on poplar · Louvre, Paris"
        />
        <p className="label-meta px-3 pt-3 pb-1">Artists</p>
        <SearchRow
          type="artist"
          initials="LV"
          primary="Leonardo da Vinci"
          secondary="Italian Renaissance · 1452–1519"
        />
      </div>
    </div>
  );
}

// ============================================================================
// 6. Map pins
// ============================================================================

function MapPinShowcase() {
  return (
    <div className="bg-[var(--color-map-land)] rounded-lg p-10 border border-[var(--color-border)] flex flex-wrap items-end gap-10">
      <PinExample label="Single pin">
        <MapPin />
      </PinExample>
      <PinExample label="Related (hollow)">
        <MapPin related />
      </PinExample>
      <PinExample label="Cluster · 3">
        <MapPin count={3} size="sm" />
      </PinExample>
      <PinExample label="Cluster · 24">
        <MapPin count={24} size="md" />
      </PinExample>
      <PinExample label="Cluster · 142">
        <MapPin count={142} size="lg" />
      </PinExample>
    </div>
  );
}

function PinExample({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3">
      <div>{children}</div>
      <p className="text-xs text-[var(--color-text-muted)]">{label}</p>
    </div>
  );
}

// ============================================================================
// 7. Patterns
// ============================================================================

function Patterns() {
  return (
    <div className="space-y-6">
      <Card variant="subtle">
        <p className="label-meta mb-2">Pattern · never empty</p>
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
          The fallback floor
        </h3>
        <p className="text-sm text-[var(--color-text-primary)] mb-2">
          Every artwork page renders three default relationship rows, regardless
          of editorial enrichment:
        </p>
        <ol className="text-sm text-[var(--color-text-primary)] space-y-1 ml-5 list-decimal">
          <li>More by [Artist] at [Museum]</li>
          <li>[Movement / school] at [Museum]</li>
          <li>More by [Artist] worldwide</li>
        </ol>
        <p className="text-sm text-[var(--color-text-muted)] mt-3">
          Editorial cards (Lineage, Dialogue, Reinterpretation) appear above
          these when data exists. Defaults are the floor, not the ceiling.
        </p>
      </Card>

      <Card variant="subtle">
        <p className="label-meta mb-2">Pattern · anti-disorientation</p>
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
          Three exits from any rabbit hole
        </h3>
        <ul className="text-sm text-[var(--color-text-primary)] space-y-1 ml-5 list-disc">
          <li><strong>Breadcrumb</strong> — ancestor entities, always visible</li>
          <li><strong>Back-pill</strong> — the previous detail page, when applicable</li>
          <li><strong>Recent history</strong> — last 5 entities visited, in the search empty state</li>
        </ul>
      </Card>

      <Card variant="subtle">
        <p className="label-meta mb-2">Pattern · search as state-loader</p>
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
          Selecting a result reconfigures the interface
        </h3>
        <p className="text-sm text-[var(--color-text-primary)]">
          On search selection, both the map and the side panel update.
          The right panel slides in immediately so the user has content to read
          while the map settles. No loading spinner.
        </p>
      </Card>
    </div>
  );
}
