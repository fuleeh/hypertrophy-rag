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
        <label className="mb-1 block font-mono text-xs text-text-muted">year</label>
        <select
          value={year || ""}
          onChange={(e) => onYearChange(e.target.value ? Number(e.target.value) : undefined)}
          className="rounded-lg border border-border/60 bg-surface/60 px-3 py-1.5 text-xs text-text-secondary hover:border-border-hover transition-colors"
        >
          <option value="">any</option>
          <option value="2024">2024+</option>
          <option value="2022">2022+</option>
          <option value="2020">2020+</option>
          <option value="2018">2018+</option>
          <option value="2015">2015+</option>
        </select>
      </div>

      <div>
        <label className="mb-1 block font-mono text-xs text-text-muted">source</label>
        <select
          value={source || ""}
          onChange={(e) => onSourceChange(e.target.value || undefined)}
          className="rounded-lg border border-border/60 bg-surface/60 px-3 py-1.5 text-xs text-text-secondary hover:border-border-hover transition-colors"
        >
          <option value="">all sources</option>
          <option value="pubmed">PubMed</option>
          <option value="semantic_scholar">Semantic Scholar</option>
        </select>
      </div>
    </div>
  );
}
