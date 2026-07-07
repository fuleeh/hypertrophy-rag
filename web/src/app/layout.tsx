import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { BackgroundEffects } from "@/components/layout/background-effects";
import { Providers } from "@/components/providers";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  title: {
    default: "HypertroHub — Evidence-Based Hypertrophy Research",
    template: "%s | HypertroHub",
  },
  description:
    "Ask any training question. Get answers backed by peer-reviewed studies with real citations, sample sizes, and key findings.",
  metadataBase: new URL(BASE_URL),
  openGraph: {
    title: "HypertroHub — Evidence-Based Hypertrophy Research",
    description:
      "Ask any training question. Get answers backed by peer-reviewed studies with real citations, sample sizes, and key findings.",
    url: BASE_URL,
    siteName: "HypertroHub",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "HypertroHub — Evidence-Based Hypertrophy Research",
    description:
      "Ask any training question. Get answers backed by peer-reviewed studies with real citations, sample sizes, and key findings.",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-text">
        <Providers>
          <BackgroundEffects />
          <Navbar />
          <main className="flex-1 pt-16">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
