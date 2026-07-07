# HypertroHub — Frontend

Next.js 16 + React 19 + Tailwind v4 frontend for the HypertroHub RAG application.

## Setup

```bash
npm install
```

## Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Requires the backend running on port 8000.

## Build

```bash
npm run build
npm start
```

## Lint

```bash
npm run lint
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page with hero, how-it-works, features, stats bar |
| `/query` | Search interface with filters, study cards, answer panel |
| `/stats` | Index statistics with paper counts, source breakdown, MeSH terms |

## Architecture

- **Server Components**: layout, home page, hero, how-it-works, features, footer, background-effects, card, badge
- **Client Components**: navbar, query page, stats page, search bar, stats bar, answer panel, filters
- **State**: React Context (`QueryContext`) with localStorage persistence
- **Styling**: Tailwind v4 with custom CSS theme (teal/cyan accent, Geist font)

## SEO

- `sitemap.ts` — auto-generated sitemap
- `robots.ts` — allows crawling, disallows `/api/`
- OpenGraph + Twitter Card metadata per page
- Set `NEXT_PUBLIC_BASE_URL` in `.env.local` for production

## Docker

```bash
docker build -t hypertrophy-rag-web .
```
