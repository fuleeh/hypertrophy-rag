import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Index Statistics",
  description:
    "Overview of the indexed hypertrophy research database — PubMed and Semantic Scholar papers, chunks, and coverage.",
  openGraph: {
    title: "Index Statistics | HypertroHub",
    description:
      "Overview of the indexed hypertrophy research database — PubMed and Semantic Scholar papers, chunks, and coverage.",
  },
};

export default function StatsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
