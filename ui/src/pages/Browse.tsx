import { useEffect, useMemo, useState } from 'react'
import { useApp } from '../app/shell'
import { CategoryChip, FilterSelector, StatusBadge } from '../components/ui'
import type { Category, Status, Story, StoryAttachment } from '../lib/api'
import { FIELD_LABELS, api } from '../lib/api'

export function BrowsePage({ storyId, onClose }: { storyId: string | null; onClose: () => void }) {
  const { emails, filter, setFilter } = useApp()
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<Category | 'all'>('all')
  const [status, setStatus] = useState<Status | 'all'>('all')
  const [selected, setSelected] = useState<string | null>(storyId)

  useEffect(() => {
    setSelected(storyId)
  }, [storyId])

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    return (emails?.emails ?? []).filter((email) => {
      if (category !== 'all' && email.category !== category) return false
      if (status !== 'all' && email.status !== status) return false
      if (!normalized) return true
      return [email.email_id, email.subject, email.review_reason ?? '', ...email.mismatch_fields]
        .join(' ')
        .toLowerCase()
        .includes(normalized)
    })
  }, [emails, query, category, status])

  if (selected) {
    return <StoryView emailId={selected} onBack={() => { setSelected(null); onClose() }} />
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black">Browse decisions</h1>
          <p className="text-sm text-ink-soft">Search the current fictional result set and inspect its trace.</p>
        </div>
        <FilterSelector filter={filter} onChange={setFilter} />
      </div>
      <div className="grid gap-3 rounded-xl border border-line bg-card p-4 shadow-sm md:grid-cols-3">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search id, subject, reason, or field"
          className="rounded-lg border border-line bg-slate-50 px-3 py-2 text-sm outline-none focus:border-primary"
        />
        <select value={category} onChange={(event) => setCategory(event.target.value as Category | 'all')} className="rounded-lg border border-line bg-slate-50 px-3 py-2 text-sm">
          <option value="all">All categories</option>
          <option value="BL_COMPARISON">BL comparison</option>
          <option value="SI_REQUEST">SI request</option>
          <option value="INVOICE_QUERY">Invoice query</option>
          <option value="GENERAL">General</option>
          <option value="SPAM">Spam</option>
        </select>
        <select value={status} onChange={(event) => setStatus(event.target.value as Status | 'all')} className="rounded-lg border border-line bg-slate-50 px-3 py-2 text-sm">
          <option value="all">All decisions</option>
          <option value="OK">OK</option>
          <option value="MISMATCH">Mismatch</option>
          <option value="NEEDS_REVIEW">Needs review</option>
        </select>
      </div>
      <div className="overflow-hidden rounded-xl border border-line bg-card shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-ink-soft">
            <tr><th className="px-4 py-3">Example</th><th className="px-4 py-3">Category</th><th className="px-4 py-3">Decision</th><th className="px-4 py-3">Reason / fields</th></tr>
          </thead>
          <tbody>
            {filtered.map((email) => (
              <tr key={email.email_id} onClick={() => setSelected(email.email_id)} className="cursor-pointer border-t border-line/60 hover:bg-primary-soft">
                <td className="px-4 py-3"><div className="font-mono text-xs font-bold text-primary">{email.email_id}</div><div className="max-w-md truncate">{email.subject}</div></td>
                <td className="px-4 py-3"><CategoryChip category={email.category} /></td>
                <td className="px-4 py-3"><StatusBadge status={email.status} /></td>
                <td className="px-4 py-3 font-mono text-xs">{email.review_reason ?? (email.mismatch_fields.join(', ') || '—')}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && <p className="p-6 text-center text-ink-soft">No examples match these filters.</p>}
      </div>
    </div>
  )
}

function AnchorLines({ attachment, field }: { attachment: StoryAttachment; field: string | null }) {
  const anchors = useMemo(() => new Set(field ? attachment.anchors[field] ?? [] : []), [attachment, field])
  return (
    <div className="max-h-64 overflow-auto rounded-lg border border-line bg-slate-50 p-3 font-mono text-sm leading-6">
      {attachment.lines.map((line, index) => (
        <div key={index} className={anchors.has(index) ? 'rounded bg-primary-soft px-2 font-bold text-primary' : 'px-2 text-ink-soft'}>
          {line || ' '}
        </div>
      ))}
    </div>
  )
}

function StoryView({ emailId, onBack }: { emailId: string; onBack: () => void }) {
  const [story, setStory] = useState<Story | null>(null)
  const [highlight, setHighlight] = useState<string | null>(null)
  useEffect(() => {
    api<Story>(`/emails/${emailId}/story`).then(setStory).catch(() => setStory(null))
  }, [emailId])

  if (!story) return <p className="py-20 text-center text-lg text-ink-soft">Loading trace…</p>
  return (
    <div className="space-y-6">
      <button type="button" onClick={onBack} className="font-semibold text-primary hover:underline">← Back to list</button>
      <section className="rounded-xl border border-line bg-card p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div><div className="font-mono text-sm font-bold text-primary">{story.email_id}</div><h1 className="mt-1 text-2xl font-bold">{story.subject}</h1><p className="mt-1 text-sm text-ink-soft">{story.classification.reason}</p></div>
          <div className="flex gap-2"><CategoryChip category={story.classification.category} /><StatusBadge status={story.verdict.status} /></div>
        </div>
        <pre className="mt-4 max-h-40 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 font-mono text-sm text-ink-soft">{story.body}</pre>
        <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold text-primary">{story.steps.map((step, index) => <span key={`${step.stage}-${index}`} className="rounded bg-primary-soft px-2 py-1">{step.stage}: {step.decision}</span>)}</div>
      </section>
      {story.attachments.length > 0 && <section className="grid gap-4 md:grid-cols-2">{story.attachments.map((attachment) => <div key={attachment.path} className="rounded-xl border border-line bg-card p-4 shadow-sm"><div className="mb-3 flex justify-between"><h2 className="font-bold">{attachment.kind}</h2><span className="font-mono text-xs text-ink-soft">{attachment.path.split('/').pop()}</span></div><AnchorLines attachment={attachment} field={highlight} /></div>)}</section>}
      {story.comparison && <section className="rounded-xl border border-line bg-card p-6 shadow-sm"><h2 className="mb-4 text-lg font-bold">Normalized SI / draft BL comparison</h2><div className="space-y-2">{Object.entries(story.comparison).map(([field, pair]) => <div key={field} onMouseEnter={() => setHighlight(field)} onMouseLeave={() => setHighlight(null)} className={`grid grid-cols-[1fr_2fr_2fr] gap-3 rounded-lg px-3 py-2 text-sm ${pair.match === false ? 'bg-mismatch-soft' : 'bg-ok-soft'}`}><span className="font-semibold">{FIELD_LABELS[field] ?? field}</span><span className="truncate font-mono">{pair.si || '—'}</span><span className="truncate font-mono">{pair.bl || '—'}</span></div>)}</div></section>}
      <section className={`rounded-xl border p-6 shadow-sm ${story.verdict.status === 'OK' ? 'border-green-200 bg-ok-soft' : story.verdict.status === 'MISMATCH' ? 'border-rose-200 bg-mismatch-soft' : 'border-amber-200 bg-review-soft'}`}><h2 className="text-xl font-black">Decision: {story.verdict.status}</h2><p className="mt-1 font-semibold">{story.verdict.detail}</p><p className="mt-1 text-sm">decided by {story.verdict.decided_by}{story.verdict.review_reason ? ` · review reason: ${story.verdict.review_reason}` : ''}</p></section>
    </div>
  )
}
