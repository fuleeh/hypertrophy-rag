"use client";

import { SearchBar } from "@/components/query/search-bar";
import { AnswerPanel } from "@/components/query/answer-panel";
import { StudyCard } from "@/components/query/study-card";
import { Filters } from "@/components/query/filters";
import { useQuery } from "@/lib/query-context";

export default function QueryPage() {
  const { result, isLoading, error, year, source, history, setYear, setSource, search, clearHistory } = useQuery();

  return (
    <div className="relative z-10 mx-auto max-w-4xl px-6 py-12">
      <div className="mb-8">
        <div className="font-mono text-sm text-accent mb-4">// query</div>
        <h1 className="text-3xl font-bold text-text md:text-4xl">Ask the Research</h1>
        <p className="mt-2 text-text-muted">
          Get evidence-based answers from peer-reviewed hypertrophy studies
        </p>
      </div>

      <SearchBar onSearch={search} isLoading={isLoading} />

      <div className="mt-6 flex items-center justify-between">
        <Filters
          year={year}
          source={source}
          onYearChange={setYear}
          onSourceChange={setSource}
        />
        {history.length > 0 && (
          <button
            onClick={clearHistory}
            className="font-mono text-xs text-text-muted hover:text-text transition-colors"
          >
            clear history
          </button>
        )}
      </div>

      {error && (
        <div className="mt-6 rounded-lg border border-danger/20 bg-danger/5 p-4 text-center text-sm text-danger">
          {error}
        </div>
      )}

      {isLoading && (
        <div className="mt-12 flex flex-col items-center gap-3">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          <span className="font-mono text-xs text-text-muted">searching studies...</span>
        </div>
      )}

      {result && !isLoading && (
        <div className="mt-8 space-y-6">
          <AnswerPanel result={result} onFollowUp={search} />

          <div>
            <div className="font-mono text-xs text-text-muted mb-4">// studies</div>
            <div className="space-y-3">
              {result.studies.map((study, i) => (
                <StudyCard key={study.pmid || study.s2_id || i} study={study} index={i + 1} />
              ))}
            </div>
          </div>
        </div>
      )}

      {!result && !isLoading && !error && history.length === 0 && (
        <div className="mt-16 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl border border-border/60 bg-surface/60">
            <svg className="h-6 w-6 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
            </svg>
          </div>
          <p className="font-mono text-xs text-text-muted">your results will appear here</p>
        </div>
      )}
    </div>
  );
}
