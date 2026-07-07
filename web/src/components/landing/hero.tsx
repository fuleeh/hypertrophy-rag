import { Button } from "@/components/ui/button";
import Link from "next/link";

export function Hero() {
  return (
    <section className="relative z-10 px-6 pt-32 pb-24 md:pt-40 md:pb-20">
      <div className="mx-auto max-w-5xl flex flex-col-reverse md:flex-row md:items-center md:justify-between gap-12 md:gap-16">
        <div className="flex-1">
          <div className="animate-fade-up font-mono text-sm text-accent">
            {"// research"}
          </div>

          <h1 className="animate-fade-up mt-4 text-4xl font-bold tracking-tight text-text sm:text-5xl md:text-6xl lg:text-7xl">
            Evidence-Based
            <br />
            Hypertrophy Research
          </h1>

          <p className="animate-fade-up mt-4 text-lg text-text-secondary font-light sm:text-xl md:text-2xl">
            Ask any training question. Get answers backed by peer-reviewed studies
            with real citations, sample sizes, and key findings.
          </p>

          <p className="animate-fade-up mt-6 max-w-lg text-base text-text-muted leading-relaxed">
            Indexed from PubMed and Semantic Scholar. Powered by hybrid retrieval
            with BM25 + semantic search and Reciprocal Rank Fusion.
          </p>

          <div className="animate-fade-up mt-8 flex flex-wrap items-center gap-3">
            <Link href="/query">
              <Button variant="outline" size="lg">
                Start Querying
                <svg className="ml-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Button>
            </Link>
            <Link href="/stats">
              <Button variant="ghost" size="lg">
                View Index
              </Button>
            </Link>
          </div>
        </div>

        <div className="animate-fade-up flex-shrink-0 hidden md:block">
          <div className="relative h-64 w-64 lg:h-80 lg:w-80">
            <div className="absolute inset-0 rounded-2xl border border-border/60 bg-surface/50 backdrop-blur-sm flex items-center justify-center">
              <div className="text-center">
                <div className="text-5xl lg:text-6xl font-bold font-mono text-accent">16k+</div>
                <div className="mt-2 text-sm text-text-muted">chunks indexed</div>
                <div className="mt-4 flex items-center justify-center gap-2 text-xs text-text-muted">
                  <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
                  live
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
