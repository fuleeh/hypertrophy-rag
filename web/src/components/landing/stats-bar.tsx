"use client";

import { useEffect, useState } from "react";
import { getStats, type Stats } from "@/lib/api";

export function StatsBar() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch(() => {
        setStats({
          total_papers: 0,
          total_chunks: 0,
          pubmed_count: 0,
          s2_count: 0,
          year_min: 0,
          year_max: 0,
          with_doi: 0,
          with_citations: 0,
          top_mesh_terms: [],
        });
      });
  }, []);

  const items = [
    { label: "papers", value: stats?.total_papers?.toLocaleString() || "—" },
    { label: "chunks", value: stats?.total_chunks?.toLocaleString() || "—" },
    { label: "sources", value: stats ? `${stats.pubmed_count + stats.s2_count}` : "—" },
    { label: "with doi", value: stats?.with_doi?.toLocaleString() || "—" },
  ];

  return (
    <section className="relative z-10 border-y border-border bg-surface/30 py-10">
      <div className="mx-auto max-w-5xl px-6">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {items.map((item) => (
            <div key={item.label} className="text-center">
              <div className="text-3xl font-bold font-mono text-text">{item.value}</div>
              <div className="mt-1 font-mono text-xs text-text-muted uppercase tracking-wider">{item.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
