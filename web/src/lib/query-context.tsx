"use client";

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";
import { queryResearch, type ResearchAnswer, type StudySummary } from "@/lib/api";

const HISTORY_KEY = "hypertrohub-history";

export interface Message {
  role: "user" | "assistant";
  content: string;
  studies?: StudySummary[];
  confidence?: string;
}

interface QueryState {
  question: string;
  result: ResearchAnswer | null;
  isLoading: boolean;
  error: string | null;
  year: number | undefined;
  source: string | undefined;
  history: Message[];
}

interface QueryContextType extends QueryState {
  setQuestion: (q: string) => void;
  setYear: (y: number | undefined) => void;
  setSource: (s: string | undefined) => void;
  search: (question: string) => Promise<void>;
  clearHistory: () => void;
}

const QueryContext = createContext<QueryContextType | null>(null);

function loadHistory(): Message[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveHistory(history: Message[]) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  } catch {
    // ignore quota errors
  }
}

export function QueryProvider({ children }: { children: ReactNode }) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<ResearchAnswer | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [year, setYear] = useState<number | undefined>(undefined);
  const [source, setSource] = useState<string | undefined>(undefined);
  const [history, setHistory] = useState<Message[]>(loadHistory);

  useEffect(() => {
    saveHistory(history);
  }, [history]);

  const search = useCallback(
    async (q: string) => {
      setQuestion(q);
      setIsLoading(true);
      setError(null);

      const userMessage: Message = { role: "user", content: q };
      setHistory((prev) => [...prev, userMessage]);

      try {
        const data = await queryResearch(q, 8, year, source);
        setResult(data);
        const assistantMessage: Message = {
          role: "assistant",
          content: data.answer,
          studies: data.studies,
          confidence: data.confidence,
        };
        setHistory((prev) => [...prev, assistantMessage]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to query research");
        setResult(null);
      } finally {
        setIsLoading(false);
      }
    },
    [year, source]
  );

  const clearHistory = useCallback(() => {
    setHistory([]);
    setResult(null);
    setError(null);
    setQuestion("");
    localStorage.removeItem(HISTORY_KEY);
  }, []);

  return (
    <QueryContext.Provider
      value={{
        question,
        result,
        isLoading,
        error,
        year,
        source,
        history,
        setQuestion,
        setYear,
        setSource,
        search,
        clearHistory,
      }}
    >
      {children}
    </QueryContext.Provider>
  );
}

export function useQuery() {
  const ctx = useContext(QueryContext);
  if (!ctx) throw new Error("useQuery must be used within QueryProvider");
  return ctx;
}
