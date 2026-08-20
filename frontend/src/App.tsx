import { useState, useRef } from 'react'
import './App.css'

interface Source {
  celex_id: string
  subdivision_id: string
  type: string
  text: string
  distance: number
  citation: string
}

interface QueryResult {
  question: string
  answer: string
  sources: Source[]
  related_questions: string[]
}

const CELEX_EURLEX: Record<string, string> = {
  '32016R0679': 'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679',
  '32019L0790': 'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L0790',
  '32022R2065': 'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R2065',
  '32022R1925': 'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R1925',
  '32016L0680': 'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016L0680',
  '32002L0058': 'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32002L0058',
}

const STARTER_QUESTIONS = [
  'What is the GDPR?',
  'What rights do data subjects have under the Digital Services Act?',
  'What does the ePrivacy Directive say about cookies?',
]

function SkeletonLoader() {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="h-4 bg-surface-container-high rounded w-full" />
      <div className="h-4 bg-surface-container-high rounded w-5/6" />
      <div className="h-4 bg-surface-container-high rounded w-full" />
      <div className="h-4 bg-surface-container-high rounded w-4/5" />
      <div className="h-4 bg-surface-container-high rounded w-3/4" />
    </div>
  )
}

export default function App() {
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QueryResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const hasContent = loading || result !== null || error !== null

  async function submit(question: string) {
    const q = question.trim()
    if (!q) return
    setSubmittedQuery(q)
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      })
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      const data: QueryResult = await res.json()
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    submit(query)
  }

  function handleChip(question: string) {
    setQuery(question)
    submit(question)
  }

  const summaryTitle = result?.question ?? submittedQuery

  return (
    <div className="flex flex-col min-h-screen">
      {/* TopAppBar */}
      <header className="bg-surface border-b border-outline-variant w-full sticky top-0 z-50">
        <div className="flex justify-between items-center w-full px-4 py-4 max-w-full mx-auto">
          <div className="flex items-center gap-2 cursor-pointer hover:bg-surface-container-low transition-colors p-2 rounded-lg">
            <span className="material-symbols-outlined text-primary" style={{ fontSize: '24px' }}>
              gavel
            </span>
            <h1 className="text-headline-md font-bold text-primary">EU Legal RAG</h1>
          </div>
          <div className="cursor-pointer hover:bg-surface-container-low transition-colors p-2 rounded-full">
            <span className="material-symbols-outlined text-primary" style={{ fontSize: '24px' }}>
              account_circle
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow flex flex-col w-full px-4 py-lg pb-xl max-w-max-width-content mx-auto gap-lg">
        {/* Search Section */}
        <section className="w-full flex flex-col gap-sm">
          <form onSubmit={handleSubmit} className="relative w-full flex items-center">
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-surface-container-lowest border border-outline rounded-lg py-3 pl-4 pr-12 text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all shadow-sm"
              placeholder="Ask a question about EU law (e.g. GDPR compliance)..."
              type="text"
            />
            <button
              type="submit"
              disabled={loading}
              className="absolute right-2 top-1/2 -translate-y-1/2 bg-primary text-on-primary rounded p-2 hover:opacity-80 transition-opacity flex items-center justify-center disabled:opacity-40"
            >
              <span
                className="material-symbols-outlined"
                style={{ fontSize: '20px', fontVariationSettings: "'FILL' 1" }}
              >
                {loading ? 'hourglass_empty' : 'send'}
              </span>
            </button>
          </form>
          {/* Landing state: starter questions. Post-result: related questions from the API. */}
          <div className="flex flex-wrap gap-2 mt-2">
            {(result?.related_questions?.length
              ? result.related_questions
              : !hasContent ? STARTER_QUESTIONS : []
            ).map((q) => (
              <span
                key={q}
                onClick={() => handleChip(q)}
                className="bg-surface-container text-secondary text-label-sm px-3 py-1 rounded-full cursor-pointer hover:bg-surface-container-high transition-colors"
              >
                {q}
              </span>
            ))}
          </div>
        </section>

        {/* Answer Section — visible only after a query is submitted */}
        {hasContent && (
          <section className="w-full bg-surface-container-lowest border border-surface-variant rounded-lg p-lg shadow-sm">
            <h2 className="text-title-lg text-primary font-semibold mb-md flex items-center gap-2 border-b border-surface-variant pb-2">
              <span className="material-symbols-outlined text-primary">auto_awesome</span>
              AI Summary{summaryTitle ? `: ${summaryTitle}` : ''}
            </h2>
            <div className="text-body-md text-on-surface">
              {loading && <SkeletonLoader />}
              {error && (
                <div className="flex items-center gap-2 text-error">
                  <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>
                    error
                  </span>
                  <span>{error}</span>
                </div>
              )}
              {result && (
                <p className="whitespace-pre-line leading-relaxed">{result.answer}</p>
              )}
            </div>
          </section>
        )}

        {/* Sources Section — visible only when results include sources */}
        {result && result.sources.length > 0 && (
          <section className="w-full flex flex-col gap-md">
            <h3 className="text-title-lg text-primary font-semibold flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">library_books</span>
              Verified Sources
            </h3>
            <div className="flex flex-col gap-sm">
              {result.sources.map((source, i) => {
                const eurLexUrl = CELEX_EURLEX[source.celex_id]
                return (
                  <div
                    key={i}
                    className="bg-[#EBF8FF] border border-[#BEE3F8] rounded-lg p-md hover:shadow-md transition-shadow cursor-pointer group"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex flex-col">
                        <span className="text-label-md font-semibold text-primary">
                          {source.citation}
                        </span>
                        <span className="text-label-sm opacity-50 text-primary mt-0.5">
                          {source.celex_id}
                        </span>
                      </div>
                      <span className="material-symbols-outlined text-primary">description</span>
                    </div>
                    <p className="text-body-md text-on-surface line-clamp-3 text-sm mt-2 opacity-80 group-hover:opacity-100 transition-opacity">
                      &ldquo;{source.text}&rdquo;
                    </p>
                    {eurLexUrl && (
                      <div className="mt-3 flex justify-end">
                        <a
                          href={eurLexUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-label-sm text-primary flex items-center gap-1 group-hover:underline"
                          onClick={(e) => e.stopPropagation()}
                        >
                          View Full Text
                          <span
                            className="material-symbols-outlined"
                            style={{ fontSize: '16px' }}
                          >
                            arrow_forward
                          </span>
                        </a>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-surface-container-low border-t border-outline-variant w-full mt-auto">
        <div className="flex flex-col md:flex-row justify-between items-center w-full px-4 py-lg max-w-full mx-auto gap-md">
          <div className="text-label-md font-semibold text-primary">
            © 2024 EU Legal RAG. Official European Union legal texts provided for information only.
          </div>
          <div className="flex gap-4">
            <a className="text-label-sm text-secondary hover:text-primary transition-colors cursor-pointer" href="#">
              Terms of Service
            </a>
            <a className="text-label-sm text-secondary hover:text-primary transition-colors cursor-pointer" href="#">
              Privacy Policy
            </a>
            <a className="text-label-sm text-secondary hover:text-primary transition-colors cursor-pointer" href="#">
              Disclaimer
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
