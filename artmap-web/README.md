# ArtMap — Web

The frontend for [ArtMap](../README.md), a global cultural atlas indexing every
museum, artist, and artwork on earth.

## Stack

- **Next.js 16** (App Router)
- **React 19**
- **TypeScript** (strict)
- **Tailwind CSS v4** (CSS-first config — see `app/globals.css`)
- **MapLibre GL** + **PMTiles** + **Protomaps** (map rendering)
- **Supabase** (data layer)

## Getting started

```bash
npm install
npm run dev
```

The app runs on `http://localhost:3000`.

## Routes

| Path | What it is |
|---|---|
| `/` | Homepage (placeholder) |
| `/map` | The main map screen |
| `/design-system` | Live reference for every component and token |

## Design system

ArtMap has a documented design system. Visit `/design-system` in the running
app to see every component, every state, and every token rendered live. Use it
as the source of truth when designing or implementing screens.

The design brief (`../artmap-brief.md`, when present) is the narrative
companion. It explains the relationship taxonomy, the anti-disorientation
system, the never-empty fallback rules, and the strategic intent behind
the visual decisions.

## Working with this codebase

If you are an AI assistant (Claude Code, Claude Design), read [`CLAUDE.md`](./CLAUDE.md)
before making changes. It documents the conventions, the hard rules, and the
Next.js 16 / Tailwind v4 specifics that differ from older patterns.

## Commands

```bash
npm run dev      # Dev server on localhost:3000
npm run build    # Production build
npm run start    # Start the production server
npm run lint     # ESLint
npm run format   # Prettier (writes changes)
```

## Project structure

```
app/
├── components/
│   ├── ui/         ← generic primitives (Button, Chip, Card)
│   ├── artmap/     ← ArtMap-specific (PolaroidCard, RelationshipCard, ...)
│   └── layout/     ← Sidebar, Breadcrumb, BackPill
├── design-system/  ← /design-system route
├── map/            ← /map route + map components
├── globals.css     ← all design tokens (Tailwind v4 @theme)
├── layout.tsx      ← root layout, loads DM Sans
└── page.tsx
lib/
└── supabase.ts
```

## Tokens

All design tokens (colors, type scale, radii) are defined in
`app/globals.css` inside the `@theme` block. **There is no `tailwind.config.ts`** —
Tailwind v4 reads `@theme` directly from CSS.

To add a token, edit `globals.css`. It becomes a Tailwind utility automatically.

## License

Private project. Bootstrapped by [@afabrizzio12](https://github.com/afabrizzio12).
