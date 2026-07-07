import { GradientText } from "@/components/ui/gradient-text";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export function Hero() {
  return (
    <section className="relative z-10 px-6 pt-32 pb-24 text-center">
      <div className="mx-auto max-w-4xl">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-1.5 text-sm text-muted">
          <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
          PubMed + Semantic Scholar indexed
        </div>

        <h1 className="text-5xl font-bold leading-tight tracking-tight md:text-7xl">
          Evidence-Based
          <br />
          <GradientText>Hypertrophy Research</GradientText>
          <br />
          at Your Fingertips
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg text-muted leading-relaxed">
          Ask any training question. Get answers backed by peer-reviewed studies
          with real citations, sample sizes, and key findings.
        </p>

        <div className="mt-10 flex items-center justify-center gap-4">
          <Link href="/query">
            <Button size="lg" className="text-base px-8">
              Start Querying
              <svg className="ml-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Button>
          </Link>
          <Link href="/stats">
            <Button variant="ghost" size="lg" className="text-base">
              View Index
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
