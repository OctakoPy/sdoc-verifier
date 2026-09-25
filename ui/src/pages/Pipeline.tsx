import { useEffect, useMemo, useState } from 'react'
import { useApp } from '../app/shell'
import { FilterSelector } from '../components/ui'
import {
  ActAttachmentOpen,
  ActCompareBoard,
  ActEmailFocus,
  ActInboxCascade,
  ActVerdict,
} from '../components/cinema/Cinema'
import type { EmailSummary, Story } from '../lib/api'
import { fetchStoryCached } from '../lib/api'

const STAGES = ['Examples', 'Email', 'Attachments', 'Comparison', 'Decision'] as const

function useStories(summaries: EmailSummary[]): Story[] {
  const [stories, setStories] = useState<Story[]>([])
  useEffect(() => {
    let cancelled = false
    Promise.all(summaries.slice(0, 8).map((summary) => fetchStoryCached(summary.email_id)))
      .then((loaded) => {
        if (!cancelled) setStories(loaded)
      })
      .catch(() => {
        if (!cancelled) setStories([])
      })
    return () => {
      cancelled = true
    }
  }, [summaries])
  return stories
}

export function PipelinePage() {
  const { filter, setFilter, emails } = useApp()
  const stories = useStories(emails?.emails ?? [])
  const [selected, setSelected] = useState(0)
  const [stage, setStage] = useState(0)
  const story = stories[selected]
  const activeStages = useMemo(() => {
    if (!story) return [0, 1, 2, 3, 4]
    return [0, 1, story.attachments.length ? 2 : -1, story.comparison ? 3 : -1, 4].filter((item) => item >= 0)
  }, [story])

  if (!emails) return <p className="py-20 text-center text-lg text-ink-soft">Loading examples…</p>
  if (!story) return <p className="py-20 text-center text-lg text-ink-soft">No trace stories are available.</p>

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black">Trace explorer</h1>
          <p className="text-sm text-ink-soft">Follow one fictional email through the deterministic stages.</p>
        </div>
        <FilterSelector filter={filter} onChange={setFilter} />
      </div>
      <div className="flex flex-wrap gap-2">
        {activeStages.map((item, position) => (
          <button
            key={STAGES[item]}
            type="button"
            onClick={() => setStage(item)}
            className={`rounded-full px-4 py-2 text-sm font-semibold ${
              stage === item ? 'bg-ink text-white' : 'border border-line bg-card text-ink-soft hover:bg-primary-soft'
            }`}
          >
            {position + 1}. {STAGES[item]}
          </button>
        ))}
      </div>
      <div className="min-h-80">
        {stage === 0 && <ActInboxCascade stories={stories} onPick={(id) => {
          const index = stories.findIndex((item) => item.email_id === id)
          if (index >= 0) {
            setSelected(index)
            setStage(1)
          }
        }} />}
        {stage === 1 && <ActEmailFocus story={story} />}
        {stage === 2 && <ActAttachmentOpen story={story} />}
        {stage === 3 && <ActCompareBoard story={story} />}
        {stage === 4 && <ActVerdict story={story} />}
      </div>
    </div>
  )
}
