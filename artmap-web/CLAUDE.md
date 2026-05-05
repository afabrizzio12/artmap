# ArtMap — `artmap-web` working notes for Claude

This document is for AI assistants (Claude Code, Claude Design) working on the
ArtMap frontend. Read it before making changes.

## What this app is

ArtMap is a global cultural atlas — every museum, artist, and artwork on earth,
navigable through the relationships between them. The product is a **network of
artistic relationships** exposed through a spatial interface. The map is one
lens among several. The relationships (lineage, dialogue, co-presence, movement,
reinterpretation) are the product.

## Stack

- **Next.js 16** with App Router. **Important: this is a recent major version.**
  Read `node_modules/next/dist/docs/` before using framework APIs you are not
  certain about. Async `params`, caching defaults, and several experimental
  flags differ from earlier versions.
- **React 19**.
- **TypeScript** (strict mode).
- **Tailwind CSS v4** — CSS-first configuration. There is **no** `tailwind.config.ts`.
  Tokens are declared in `app/globals.css` inside an `@theme` block. To add
  colors, sizes, fonts, or radii: edit `globals.css`, not a JS config.
- **MapLibre GL** (with PMTiles + Protomaps) for the map.
- **Supabase** for the data layer.
- **npm** as the package manager.

## Repository structure (within `artmap-web/`)

```
artmap-web/
├── app/
│   ├── components/
│   │   ├── ui/         ← generic primitives (Button, Chip, Card)
│   │   ├── artmap/     ← ArtMap-specific (PolaroidCard, RelationshipCard, ...)
│   │   └── layout/     ← Sidebar, Breadcrumb, BackPill
│   ├── design-system/  ← live design system reference page (/design-system route)
│   ├── map/            ← /map route — existing map components (MapClient, MapWrapper, SidePanel)
│   ├── globals.css     ← all design tokens (Tailwind v4 @theme)
│   ├── layout.tsx      ← root layout, loads DM Sans
│   └── page.tsx
├── lib/
│   └── supabase.ts
├── eslint.config.mjs
├── .prettierrc.json
├── next.config.ts
├── package.json
└── tsconfig.json
```

## Design system

The complete visual reference is at the `/design-system` route. Run `npm run dev`
and visit `http://localhost:3000/design-system` to see every component, every
state, and every token rendered live. **Use this page as the source of truth
when designing or implementing new screens.**

The design brief (`artmap-brief.md` at the repo root, when present) is the
narrative companion to this page.

### Hard rules

These are non-negotiable. If you find yourself violating one, stop and ask the
human.

1. **Polaroid cards never render without an image.** If `imageUrl` is missing,
   the component returns `null`. Do not add a placeholder. ArtMap loses meaning
   without images, and the data layer is responsible for ensuring every surfaced
   entity has one. See `PolaroidCard.tsx`.

2. **Pale gold `--color-callout` is for count callouts only.** Never use it as
   a general accent, hover state, or decorative color. The accent color is
   steel blue `--color-accent`. Mixing the two breaks the visual hierarchy.

3. **No exact counts are ever approximated.** "100+" or "1.2k" are forbidden.
   Always show exact numbers. Tabular numerals via the `.tabular` utility.

4. **Tone: intellectual, calm, editorial.** No gamification, no badges, no star
   ratings, no playful gradients, no noisy iconography, no emoji. If a design
   decision is drifting toward "SaaS dashboard" or "tourist app," push back.

5. **Search is a state-loader, not just a navigation tool.** Selecting a result
   reconfigures both the map and the side panel simultaneously. See the brief
   for full behavior matrix.

6. **Five relationship types only.** Lineage, Dialogue, Co-presence, Movement,
   Reinterpretation. No new categories. New nuances become tags inside an
   existing type, not new types. Priority order for display: Lineage > Dialogue
   > Co-presence > Movement > Reinterpretation.

7. **Never empty.** Every detail page renders default fallback relationship
   rows even when editorial data is absent. The defaults are the floor, not
   the ceiling.

## Tokens — how to add or change one

All design tokens live in `app/globals.css` inside the `@theme` block.

To add a new color (example):

```css
@theme {
  --color-success: #4f7a4a;
}
```

This automatically becomes available as Tailwind utilities: `bg-success`,
`text-success`, `border-success`, etc. **Do not** create a `tailwind.config.ts`
— Tailwind v4 reads `@theme` directly.

To use a token in a component, prefer the CSS variable form
`var(--color-accent)` over the Tailwind utility for clarity in arbitrary value
positions. For standard utilities (`bg-`, `text-`, `border-`), Tailwind
utilities are fine.

## Conventions

### Components

- Functional components. No classes.
- Props typed with TypeScript interfaces, not types, when extensible.
- Server components by default. Add `'use client'` only when interactive state
  or browser APIs are required. Most ArtMap components are server-renderable.
- One component per file. File name matches export name (PascalCase).
- No barrel `index.ts` files in `components/` — import from full paths.

### Styling

- Tailwind utility classes for layout and spacing.
- CSS variables (`var(--color-*)`) for color values inside `className`
  arbitrary values. This keeps the palette centralized.
- No inline styles unless dynamic (e.g., a width set by a prop).
- No CSS modules. Tailwind only.

### Imports

- Use `@/` path alias for absolute imports from the `artmap-web/` root.
  Configured in `tsconfig.json`.

### Accessibility

- All interactive elements have visible focus states using the `focus-visible`
  pseudo-class with `outline-2` and `outline-[var(--color-accent)]`.
- Minimum 44×44px tap targets.
- Images require non-empty alt text. Decorative images use `alt=""` explicitly.
- Color is never the sole carrier of information.

## Commands

```bash
npm run dev      # Start the dev server on localhost:3000
npm run build    # Production build
npm run start    # Start the production server
npm run lint     # Run ESLint
npm run format   # Run Prettier (writes changes)
```

## When you're stuck

- Re-read the relevant section of the design brief at the repo root.
- Visit `/design-system` in the running app.
- For Next.js 16 specifics: `node_modules/next/dist/docs/`.
- For Tailwind v4 specifics: the project uses CSS-first config, not the v3
  JS-config style. Don't import from training data — verify against the
  installed version's docs if uncertain.

---

*Last updated by Claude during the design system v1 rollout.*
