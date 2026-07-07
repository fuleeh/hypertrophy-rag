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
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="relative z-10 mx-auto max-w-4xl px-6 py-12 text-center">
        <h1 className="text-3xl font-bold">Index Statistics</h1>
        <p className="mt-4 text-muted">
          No index found. Run <code className="rounded bg-surface px-2 py-1 text-accent">hypertrophy-rag ingest</code> to populate the database.
        </p>
      </div>
    );
  }

  return (
    <div className="relative z-10 mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-3xl font-bold md:text-4xl">Index Statistics</h1>
      <p className="mt-2 text-muted">Overview of the indexed research database</p>

      {/* Main stats */}
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total Papers", value: stats.total_papers.toLocaleString(), color: "text-accent" },
          { label: "Total Chunks", value: stats.total_chunks.toLocaleString(), color: "text-accent" },
          { label: "With DOI", value: stats.with_doi.toLocaleString(), color: "text-success" },
          { label: "With Citations", value: stats.with_citations.toLocaleString(), color: "text-success" },
        ].map((item) => (
          <Card key={item.label} className="text-center">
            <div className={`text-3xl font-bold ${item.color}`}>{item.value}</div>
            <div className="mt-1 text-sm text-muted">{item.label}</div>
          </Card>
        ))}
      </div>

      {/* Source breakdown */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <Card>
          <h3 className="mb-3 text-sm font-bold text-muted">Source Breakdown</h3>
          <div className="space-y-3">
            <div>
              <div className="mb-1 flex justify-between text-sm">
                <span>PubMed</span>
                <span className="text-muted">{stats.pubmed_count.toLocaleString()}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-teal-500 to-teal-400"
                  style={{
                    width: `${stats.total_papers ? (stats.pubmed_count / stats.total_papers) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
            <div>
              <div className="mb-1 flex justify-between text-sm">
                <span>Semantic Scholar</span>
                <span className="text-muted">{stats.s2_count.toLocaleString()}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-teal-400"
                  style={{
                    width: `${stats.total_papers ? (stats.s2_count / stats.total_papers) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <h3 className="mb-3 text-sm font-bold text-muted">Year Range</h3>
          <div className="flex items-center gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{stats.year_min || "—"}</div>
              <div className="text-xs text-muted">Oldest</div>
            </div>
            <div className="flex-1 h-px bg-border" />
            <div className="text-center">
              <div className="text-2xl font-bold">{stats.year_max || "—"}</div>
              <div className="text-xs text-muted">Newest</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Top MeSH terms */}
      {stats.top_mesh_terms.length > 0 && (
        <div className="mt-8">
          <Card>
            <h3 className="mb-4 text-sm font-bold text-muted">Top MeSH Terms</h3>
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
