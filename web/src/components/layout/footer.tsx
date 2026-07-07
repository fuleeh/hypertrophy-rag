export function Footer() {
  return (
    <footer className="border-t border-border py-8">
      <div className="mx-auto max-w-5xl px-6">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-text-muted">
              HH
            </span>
            <span className="text-xs text-text-muted">
              HypertroHub
            </span>
          </div>
          <div className="flex items-center gap-6 text-xs text-text-muted">
            <span>PubMed + Semantic Scholar</span>
            <span>LLM: Groq</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
