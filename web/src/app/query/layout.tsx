import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Query",
  description:
    "Search peer-reviewed hypertrophy studies. Get evidence-based answers with citations, sample sizes, and key findings.",
  openGraph: {
    title: "Query | HypertroHub",
    description:
      "Search peer-reviewed hypertrophy studies. Get evidence-based answers with citations, sample sizes, and key findings.",
  },
};

export default function QueryLayout({ children }: { children: React.ReactNode }) {
  return children;
}
