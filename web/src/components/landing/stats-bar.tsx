"use client";

import { useEffect, useState } from "react";
import { getStats, type Stats } from "@/lib/api";

export function StatsBar() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch(() => {
        // API not available, show defaults
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
    { label: "Papers", value: stats?.total_papers?.toLocaleString() || "—" },
    { label: "Chunks", value: stats?.total_chunks?.toLocaleString() || "—" },
    { label: "Sources", value: stats ? `${stats.pubmed_count + stats.s2_count}` : "—" },
    { label: "With DOI", value: stats?.with_doi?.toLocaleString() || "—" },
  ];

  return (
    <section className="relative z-10 border-y border-border bg-surface/50 py-8">
      <div className="mx-auto max-w-5xl px-6">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {items.map((item) => (
            <div key={item.label} className="text-center">
              <div className="text-3xl font-bold gradient-text">{item.value}</div>
              <div className="mt-1 text-sm text-muted">{item.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
