import { createContext, useContext, useEffect, useState } from 'react'
import type { EmailList, Filter } from '../lib/api'
import { api } from '../lib/api'
import { BrowsePage } from '../pages/Browse'
import { OverviewPage } from '../pages/Overview'
import { PipelinePage } from '../pages/Pipeline'

type Page = 'overview' | 'pipeline' | 'browse'

const PAGES: { id: Page; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'pipeline', label: 'Trace' },
  { id: 'browse', label: 'Browse' },
]

interface AppState {
  filter: Filter
  setFilter: (filter: Filter) => void
  emails: EmailList | null
  openStory: (emailId: string) => void
}

const AppContext = createContext<AppState>({
  filter: 'all',
  setFilter: () => undefined,
  emails: null,
  openStory: () => undefined,
})

export function useApp() {
  return useContext(AppContext)
}

export function Shell() {
  const [page, setPage] = useState<Page>('overview')
  const [filter, setFilter] = useState<Filter>('all')
  const [emails, setEmails] = useState<EmailList | null>(null)
  const [storyId, setStoryId] = useState<string | null>(null)

  useEffect(() => {
    api<EmailList>(`/emails?subset=${filter}`)
      .then(setEmails)
      .catch(() => setEmails(null))
  }, [filter])

  function openStory(emailId: string) {
    setStoryId(emailId)
    setPage('browse')
  }

  return (
    <AppContext.Provider value={{ filter, setFilter, emails, openStory }}>
      <div className="min-h-screen">
        <header className="sticky top-0 z-20 border-b border-line bg-white/90 backdrop-blur">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
            <div>
              <div className="text-xl font-black tracking-tight text-ink">SDOC Verifier</div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-soft">
                Auditable shipping-document decisions
              </div>
            </div>
            <nav className="flex flex-wrap gap-1 rounded-full border border-line bg-slate-100 p-1">
              {PAGES.map(({ id, label }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setPage(id)}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    page === id ? 'bg-primary text-white shadow' : 'text-ink-soft hover:text-primary'
                  }`}
                >
                  {label}
                </button>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">
          {page === 'overview' && <OverviewPage />}
          {page === 'pipeline' && <PipelinePage />}
          {page === 'browse' && <BrowsePage storyId={storyId} onClose={() => setStoryId(null)} />}
        </main>
      </div>
    </AppContext.Provider>
  )
}
