"use client";

interface FiltersProps {
  year: number | undefined;
  source: string | undefined;
  onYearChange: (year: number | undefined) => void;
  onSourceChange: (source: string | undefined) => void;
}

export function Filters({ year, source, onYearChange, onSourceChange }: FiltersProps) {
  return (
    <div className="flex flex-wrap gap-3">
      <div>
        <label className="mb-1 block text-xs text-muted">Min Year</label>
        <select
          value={year || ""}
          onChange={(e) => onYearChange(e.target.value ? Number(e.target.value) : undefined)}
          className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-foreground hover:border-border-hover transition-colors"
        >
          <option value="">Any</option>
          <option value="2024">2024+</option>
          <option value="2022">2022+</option>
          <option value="2020">2020+</option>
          <option value="2018">2018+</option>
          <option value="2015">2015+</option>
        </select>
      </div>

      <div>
        <label className="mb-1 block text-xs text-muted">Source</label>
        <select
          value={source || ""}
          onChange={(e) => onSourceChange(e.target.value || undefined)}
          className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-foreground hover:border-border-hover transition-colors"
        >
          <option value="">All Sources</option>
          <option value="pubmed">PubMed</option>
          <option value="semantic_scholar">Semantic Scholar</option>
        </select>
      </div>
    </div>
  );
}
