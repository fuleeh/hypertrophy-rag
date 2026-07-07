export function Footer() {
  return (
    <footer className="border-t border-border py-8">
      <div className="mx-auto max-w-6xl px-6">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-violet-500 to-fuchsia-500">
              <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5m-4.25-11.398c.251.023.501.05.75.082M12 21a8.966 8.966 0 005.982-2.275M12 21a8.966 8.966 0 01-5.982-2.275M15.75 3.186a24.284 24.284 0 012.082.763m-9.916.763a24.284 24.284 0 00-2.082.763M3.75 12.763c.577.272 1.177.458 1.793.558m12.926-.558c.577-.1 1.15-.286 1.693-.558" />
              </svg>
            </div>
            <span className="text-sm font-medium text-muted">
              HypertroHub — Evidence-Based Research
            </span>
          </div>
          <div className="flex items-center gap-6 text-sm text-muted">
            <span>Data: PubMed + Semantic Scholar</span>
            <span>LLM: Groq</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
