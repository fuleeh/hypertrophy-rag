"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getStats, type Stats } from "@/lib/api";

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="relative z-10 flex items-center justify-center py-32">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="relative z-10 mx-auto max-w-4xl px-6 py-12 text-center">
        <div className="font-mono text-sm text-accent mb-4">{"// stats"}</div>
        <h1 className="text-3xl font-bold text-text">Index Statistics</h1>
        <p className="mt-4 text-text-muted">
          No index found. Run <code className="rounded bg-surface px-2 py-1 font-mono text-xs text-accent border border-border/60">hypertrophy-rag ingest</code> to populate the database.
        </p>
      </div>
    );
  }

  return (
    <div className="relative z-10 mx-auto max-w-4xl px-6 py-12">
      <div className="font-mono text-sm text-accent mb-4">{"// stats"}</div>
      <h1 className="text-3xl font-bold text-text md:text-4xl">Index Statistics</h1>
      <p className="mt-2 text-text-muted">Overview of the indexed research database</p>

      {/* Main stats */}
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "papers", value: stats.total_papers.toLocaleString(), color: "text-text" },
          { label: "chunks", value: stats.total_chunks.toLocaleString(), color: "text-text" },
          { label: "with doi", value: stats.with_doi.toLocaleString(), color: "text-accent" },
          { label: "cited", value: stats.with_citations.toLocaleString(), color: "text-accent" },
        ].map((item) => (
          <Card key={item.label} className="text-center">
            <div className={`text-2xl font-bold font-mono ${item.color}`}>{item.value}</div>
            <div className="mt-1 font-mono text-xs text-text-muted uppercase tracking-wider">{item.label}</div>
          </Card>
        ))}
      </div>

      {/* Source breakdown */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <Card>
          <h3 className="mb-3 font-mono text-xs text-text-muted uppercase tracking-wider">Source Breakdown</h3>
          <div className="space-y-3">
            <div>
              <div className="mb-1 flex justify-between text-sm">
                <span className="text-text-secondary">PubMed</span>
                <span className="font-mono text-xs text-text-muted">{stats.pubmed_count.toLocaleString()}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-accent"
                  style={{
                    width: `${stats.total_papers ? (stats.pubmed_count / stats.total_papers) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
            <div>
              <div className="mb-1 flex justify-between text-sm">
                <span className="text-text-secondary">Semantic Scholar</span>
                <span className="font-mono text-xs text-text-muted">{stats.s2_count.toLocaleString()}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-teal-400"
                  style={{
                    width: `${stats.total_papers ? (stats.s2_count / stats.total_papers) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <h3 className="mb-3 font-mono text-xs text-text-muted uppercase tracking-wider">Year Range</h3>
          <div className="flex items-center gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold font-mono text-text">{stats.year_min || "—"}</div>
              <div className="font-mono text-xs text-text-muted">oldest</div>
            </div>
            <div className="flex-1 h-px bg-border" />
            <div className="text-center">
              <div className="text-2xl font-bold font-mono text-text">{stats.year_max || "—"}</div>
              <div className="font-mono text-xs text-text-muted">newest</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Top MeSH terms */}
      {stats.top_mesh_terms.length > 0 && (
        <div className="mt-8">
          <Card>
            <h3 className="mb-4 font-mono text-xs text-text-muted uppercase tracking-wider">Top MeSH Terms</h3>
            <div className="flex flex-wrap gap-2">
              {stats.top_mesh_terms.map(([term, count]) => (
                <Badge key={term} variant="accent">
                  {term} ({count})
                </Badge>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
