import { Hero } from "@/components/landing/hero";
import { HowItWorks } from "@/components/landing/how-it-works";
import { Features } from "@/components/landing/features";
import { StatsBar } from "@/components/landing/stats-bar";
import Link from "next/link";

export default function Home() {
  return (
    <>
      <Hero />
      <StatsBar />
      <HowItWorks />
      <Features />

      {/* Final CTA */}
      <section className="relative z-10 px-6 py-24 text-center">
        <div className="mx-auto max-w-2xl">
          <div className="font-mono text-sm text-accent mb-4">{"// ready?"}</div>
          <h2 className="text-3xl font-bold text-text md:text-4xl">
            Start training smarter
          </h2>
          <p className="mt-4 text-text-muted text-lg">
            Stop guessing. Start using the evidence.
          </p>
          <Link
            href="/query"
            className="mt-8 inline-flex h-11 items-center rounded-full border border-border px-6 text-sm font-medium text-text-secondary transition-all duration-200 hover:border-border-hover hover:text-text"
          >
            Ask a Question
            <svg className="ml-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </section>
    </>
  );
}
