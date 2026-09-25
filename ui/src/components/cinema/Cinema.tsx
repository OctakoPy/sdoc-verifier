import type { Story } from '../../lib/api'
import { FIELD_LABELS } from '../../lib/api'
import { CategoryChip, StatusBadge } from '../ui'

export function ActInboxCascade({ stories, onPick }: { stories: Story[]; onPick: (emailId: string) => void }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {stories.map((story) => (
        <button
          key={story.email_id}
          type="button"
          onClick={() => onPick(story.email_id)}
          className="rounded-xl border border-line bg-card p-4 text-left shadow-sm transition hover:border-primary hover:bg-primary-soft"
        >
          <div className="font-mono text-xs font-bold text-primary">{story.email_id}</div>
          <div className="mt-1 line-clamp-2 font-semibold">{story.subject}</div>
          <div className="mt-3"><CategoryChip category={story.classification.category} /></div>
        </button>
      ))}
    </div>
  )
}

export function ActEmailFocus({ story }: { story: Story }) {
  return (
    <div className="rounded-xl border border-line bg-card p-6 shadow-sm">
      <div className="font-mono text-sm font-bold text-primary">{story.email_id}</div>
      <h2 className="mt-1 text-2xl font-bold">{story.subject}</h2>
      <pre className="mt-4 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 font-mono text-sm text-ink-soft">
        {story.body}
      </pre>
      <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-ink-soft">
        <CategoryChip category={story.classification.category} />
        <span>{story.classification.reason}</span>
        <span>confidence {story.classification.confidence?.toFixed(2) ?? '—'}</span>
      </div>
    </div>
  )
}

export function ActAttachmentOpen({ story }: { story: Story }) {
  if (story.attachments.length === 0) {
    return <p className="rounded-xl border border-line bg-card p-6 text-ink-soft">This example has no attachments.</p>
  }
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {story.attachments.map((attachment) => (
        <div key={attachment.path} className="rounded-xl border border-line bg-card p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between gap-2">
            <h3 className="font-bold">{attachment.kind}</h3>
            <div className="flex gap-2">
              {attachment.scanned && <span className="rounded bg-review-soft px-2 py-0.5 text-xs font-bold text-review">SCAN</span>}
              {attachment.translated && <span className="rounded bg-primary-soft px-2 py-0.5 text-xs font-bold text-primary">ASSISTED</span>}
            </div>
          </div>
          <div className="max-h-72 overflow-auto rounded-lg bg-slate-50 p-3 font-mono text-sm leading-6">
            {attachment.lines.map((line, index) => <div key={index}>{line || ' '}</div>)}
          </div>
        </div>
      ))}
    </div>
  )
}

export function ActCompareBoard({ story }: { story: Story }) {
  if (!story.comparison) {
    return <p className="rounded-xl border border-line bg-card p-6 text-ink-soft">No field comparison was reached for this example.</p>
  }
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-[1fr_2fr_2fr] gap-4 px-4 text-xs font-bold uppercase tracking-wide text-ink-soft">
        <span>Field</span><span>SI</span><span>Draft BL</span>
      </div>
      {Object.entries(story.comparison).map(([field, pair]) => (
        <div
          key={field}
          className={`grid grid-cols-[1fr_2fr_2fr] items-center gap-4 rounded-lg px-4 py-2 text-sm ${
            pair.match === false ? 'bg-mismatch-soft' : 'bg-ok-soft'
          }`}
        >
          <span className="font-semibold">{FIELD_LABELS[field] ?? field}</span>
          <span className="truncate font-mono">{pair.si || '—'}</span>
          <span className="truncate font-mono">{pair.bl || '—'}</span>
        </div>
      ))}
    </div>
  )
}

export function ActVerdict({ story }: { story: Story }) {
  const tone = story.verdict.status === 'OK'
    ? 'border-green-200 bg-ok-soft text-ok'
    : story.verdict.status === 'MISMATCH'
      ? 'border-rose-200 bg-mismatch-soft text-mismatch'
      : 'border-amber-200 bg-review-soft text-review'
  return (
    <div className={`rounded-xl border p-6 shadow-sm ${tone}`}>
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-2xl font-black">Decision: {story.verdict.status}</h2>
        <StatusBadge status={story.verdict.status} />
      </div>
      <p className="mt-2 font-semibold">{story.verdict.detail}</p>
      <p className="mt-1 text-sm">
        decided by {story.verdict.decided_by}
        {story.verdict.review_reason ? ` · review reason: ${story.verdict.review_reason}` : ''}
      </p>
      {story.verdict.mismatch_fields.length > 0 && (
        <p className="mt-3 font-mono text-sm">Mismatched fields: {story.verdict.mismatch_fields.join(', ')}</p>
      )}
    </div>
  )
}
