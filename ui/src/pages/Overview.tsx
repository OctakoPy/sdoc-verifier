import { useEffect, useMemo, useState } from 'react'
import { useApp } from '../app/shell'
import { CategoryChip, StatCard, StatusBadge } from '../components/ui'
import type { EmailList, EmailSummary, Overview } from '../lib/api'
import { api } from '../lib/api'

export function OverviewPage() {
  const { emails, openStory } = useApp()
  const [overview, setOverview] = useState<Overview | null>(null)
  const [allEmails, setAllEmails] = useState<EmailList | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([api<Overview>('/overview'), api<EmailList>('/emails?subset=all')])
      .then(([nextOverview, nextEmails]) => {
        setOverview(nextOverview)
        setAllEmails(nextEmails)
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : String(reason)))
  }, [])

  const mismatches = useMemo(
    () => allEmails?.emails.filter((email) => email.status === 'MISMATCH') ?? [],
    [allEmails],
  )

  if (error) {
    return <p className="rounded-xl border border-rose-200 bg-mismatch-soft p-6 text-ink">{error}</p>
  }
  if (!overview) {
    return <p className="py-20 text-center text-lg text-ink-soft">Loading local decisions…</p>
  }

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-blue-200 bg-primary-soft p-6">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">Local fictional demo</p>
        <h1 className="mt-2 text-3xl font-black text-ink">Deterministic evidence, explicit review.</h1>
        <p className="mt-2 max-w-3xl text-ink-soft">
          This dashboard shows decisions for independently authored synthetic examples. It is an in-distribution
          demonstration, not independent real-world validation.
        </p>
      </section>

      <section className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard value={overview.total_emails} label="Examples" />
        <StatCard value={overview.status_distribution.OK} label="OK" />
        <StatCard value={overview.status_distribution.MISMATCH} label="Mismatches" />
        <StatCard value={overview.status_distribution.NEEDS_REVIEW} label="Needs review" />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-line bg-card p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-bold">Email categories</h2>
          <div className="space-y-3">
            {Object.entries(overview.category_distribution).map(([category, count]) => (
              <div key={category} className="flex items-center justify-between text-sm">
                <span className="font-semibold">{category.replace(/_/g, ' ')}</span>
                <span className="font-mono text-primary">{count}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-line bg-card p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-bold">Review reasons</h2>
          <div className="space-y-3">
            {Object.entries(overview.review_reasons).map(([reason, count]) => (
              <div key={reason} className="flex items-center justify-between rounded-lg bg-review-soft px-3 py-2 text-sm">
                <span className="font-mono font-semibold text-review">{reason}</span>
                <span className="font-mono font-bold text-review">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-bold">Mismatch decisions</h2>
          <span className="rounded-md bg-mismatch-soft px-3 py-1 text-sm font-bold text-mismatch">{mismatches.length}</span>
        </div>
        {mismatches.length === 0 ? (
          <p className="rounded-xl border border-line bg-card p-6 text-ink-soft">No mismatches in this result set.</p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-line bg-card shadow-sm">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-ink-soft">
                <tr>
                  <th className="px-4 py-3">Example</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Fields</th>
                </tr>
              </thead>
              <tbody>
                {mismatches.map((email: EmailSummary) => (
                  <tr
                    key={email.email_id}
                    onClick={() => openStory(email.email_id)}
                    className="cursor-pointer border-t border-line/60 hover:bg-primary-soft"
                  >
                    <td className="px-4 py-3">
                      <div className="font-mono text-xs font-bold text-primary">{email.email_id}</div>
                      <div className="max-w-md truncate">{email.subject}</div>
                    </td>
                    <td className="px-4 py-3"><CategoryChip category={email.category} /></td>
                    <td className="px-4 py-3"><StatusBadge status={email.status} /></td>
                    <td className="px-4 py-3 font-mono text-xs">{email.mismatch_fields.join(', ') || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="text-center text-xs text-ink-soft">
        Read-only view · no email sending, persistence, or cloud calls · {emails?.count ?? 0} records currently selected
      </p>
    </div>
  )
}
