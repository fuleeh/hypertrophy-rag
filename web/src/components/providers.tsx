"use client";

import { QueryProvider } from "@/lib/query-context";

export function Providers({ children }: { children: React.ReactNode }) {
  return <QueryProvider>{children}</QueryProvider>;
}
