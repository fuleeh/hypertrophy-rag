"use client";

import { Badge } from "@/components/ui/badge";
import type { ResearchAnswer } from "@/lib/api";

interface AnswerPanelProps {
  result: ResearchAnswer;
  onFollowUp?: (question: string) => void;
}

const FOLLOW_UP_SUGGESTIONS = [
  "What about for beginners vs advanced lifters?",
  "How does this compare to the latest meta-analysis?",
  "What are the practical takeaways for programming?",
];

export function AnswerPanel({ result, onFollowUp }: AnswerPanelProps) {
  const confidenceColors: Record<string, "success" | "warning" | "muted"> = {
    high: "success",
    medium: "warning",
    low: "muted",
  };

  return (
    <div className="rounded-xl border border-border bg-surface p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-bold">Research Summary</h2>
        <Badge variant={confidenceColors[result.confidence] || "muted"}>
          Confidence: {result.confidence}
        </Badge>
      </div>

      <div className="prose prose-invert max-w-none">
        <p className="text-foreground/90 leading-relaxed whitespace-pre-wrap">
          {result.answer}
        </p>
      </div>

      {result.conflicting_findings && (
        <div className="mt-4 rounded-lg border border-warning/30 bg-warning/5 p-4">
          <h3 className="mb-1 text-sm font-bold text-warning">Conflicting Findings</h3>
          <p className="text-sm text-muted">{result.conflicting_findings}</p>
        </div>
      )}

      <div className="mt-4 flex items-center gap-4 text-sm text-muted">
        <span>{result.studies.length} studies found</span>
        {result.studies.some((s) => s.citation_count) && (
          <span>
            • {result.studies.filter((s) => s.citation_count).length} with citation data
          </span>
        )}
      </div>

      {onFollowUp && (
        <div className="mt-6 border-t border-border pt-4">
          <p className="mb-3 text-sm font-medium text-muted">Follow up:</p>
          <div className="flex flex-wrap gap-2">
            {FOLLOW_UP_SUGGESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => onFollowUp(q)}
                className="rounded-lg border border-border bg-surface-hover px-3 py-1.5 text-xs text-foreground/80 transition-colors hover:border-accent hover:text-accent"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
