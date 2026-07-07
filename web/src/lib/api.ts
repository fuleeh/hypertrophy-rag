const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface StudySummary {
  pmid: string | null;
  s2_id: string | null;
  title: string;
  authors: string;
  year: number;
  journal: string;
  doi: string | null;
  citation_count: number | null;
  open_access_pdf: string | null;
  sample_size: string | null;
  duration: string | null;
  key_findings: string[];
  relevance_note: string;
}

export interface ResearchAnswer {
  question: string;
  answer: string;
  studies: StudySummary[];
  conflicting_findings: string | null;
  confidence: string;
}

export interface Paper {
  id: string;
  source: string;
  title: string;
  authors: string;
  abstract: string;
  year: number;
  journal: string;
  doi: string | null;
  pmid: string | null;
  citation_count: number | null;
  open_access_pdf: string | null;
  mesh_terms: string[];
}

export interface Stats {
  total_papers: number;
  total_chunks: number;
  pubmed_count: number;
  s2_count: number;
  year_min: number;
  year_max: number;
  with_doi: number;
  with_citations: number;
  top_mesh_terms: [string, number][];
}

export interface Topic {
  name: string;
  type: "pubmed" | "semantic_scholar";
  description: string;
}

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "API request failed");
  }
  return res.json();
}

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export async function queryResearch(
  question: string,
  topK: number = 8,
  year?: number,
  source?: string,
  engine: string = "custom",
  history?: Message[]
): Promise<ResearchAnswer> {
  const params = new URLSearchParams({ question, top_k: String(topK), engine });
  if (year) params.set("year", String(year));
  if (source) params.set("source", source);
  if (history && history.length > 0) {
    params.set("history", JSON.stringify(history));
  }
  return fetchAPI<ResearchAnswer>(`/api/query?${params}`);
}

export async function getStats(): Promise<Stats> {
  return fetchAPI<Stats>("/api/stats");
}

export async function getPapers(
  search?: string,
  limit: number = 50,
  offset: number = 0
): Promise<Paper[]> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (search) params.set("search", search);
  return fetchAPI<Paper[]>(`/api/papers?${params}`);
}

export async function getPaper(id: string): Promise<Paper> {
  return fetchAPI<Paper>(`/api/papers/${encodeURIComponent(id)}`);
}

export async function getTopics(): Promise<Topic[]> {
  return fetchAPI<Topic[]>("/api/topics");
}

export async function ingest(
  source: string = "all",
  topic?: string,
  maxPapers: number = 2000
): Promise<{ status: string; indexed: number }> {
  return fetchAPI("/api/ingest", {
    method: "POST",
    body: JSON.stringify({ source, topic, max_papers: maxPapers }),
  });
}
