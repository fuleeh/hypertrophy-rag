import { Hero } from "@/components/landing/hero";
import { HowItWorks } from "@/components/landing/how-it-works";
import { Features } from "@/components/landing/features";
import { StatsBar } from "@/components/landing/stats-bar";

export default function Home() {
  return (
    <>
      <Hero />
      <StatsBar />
      <HowItWorks />
      <Features />

      {/* Final CTA */}
      <section className="relative z-10 px-6 py-24 text-center">
        <h2 className="text-3xl font-bold md:text-4xl">
          Ready to Train Smarter?
        </h2>
        <p className="mt-4 text-muted text-lg">
          Stop guessing. Start using the evidence.
        </p>
        <a
          href="/query"
          className="mt-8 inline-flex h-12 items-center rounded-lg bg-gradient-to-r from-violet-500 via-purple-500 to-fuchsia-500 px-8 text-base font-medium text-white transition-all duration-300 hover:shadow-[0_0_30px_rgba(139,92,246,0.4)] hover:-translate-y-0.5"
        >
          Ask a Question
          <svg className="ml-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </a>
      </section>
    </>
  );
}
