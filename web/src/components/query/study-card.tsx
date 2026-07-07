import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { StudySummary } from "@/lib/api";

interface StudyCardProps {
  study: StudySummary;
  index: number;
}

export function StudyCard({ study, index }: StudyCardProps) {
  return (
    <Card className="group">
      <div className="flex items-start gap-4">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-accent/10 font-mono text-xs font-bold text-accent">
          {index}
        </div>

        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-bold leading-snug text-text group-hover:text-accent transition-colors">
            {study.title}
          </h3>

          <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-text-muted">
            <span>{study.authors}</span>
            <span>·</span>
            <span>{study.year}</span>
            <span>·</span>
            <span className="truncate">{study.journal}</span>
          </div>

          <div className="mt-2.5 flex flex-wrap gap-1.5">
            {study.sample_size && (
              <Badge variant="accent">n={study.sample_size}</Badge>
            )}
            {study.duration && (
              <Badge variant="accent">{study.duration}</Badge>
            )}
            {study.citation_count && (
              <Badge variant="success">{study.citation_count} citations</Badge>
            )}
            {study.pmid && (
              <Badge variant="muted">PMID: {study.pmid}</Badge>
            )}
          </div>

          {study.key_findings.length > 0 && (
            <div className="mt-3 space-y-1">
              {study.key_findings.slice(0, 3).map((finding, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-accent" />
                  <span className="text-text-muted">{finding}</span>
                </div>
              ))}
            </div>
          )}

          {study.doi && (
            <div className="mt-2.5">
              <a
                href={`https://doi.org/${study.doi}`}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono text-xs text-text-muted hover:text-accent transition-colors"
              >
                DOI: {study.doi} ↗
              </a>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
