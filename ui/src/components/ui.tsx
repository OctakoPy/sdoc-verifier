import type { Category, Filter, Status } from '../lib/api'

const FILTERS: { id: Filter; label: string }[] = [
  { id: 'starter', label: 'Starter set' },
  { id: 'comparisons', label: 'Document checks' },
  { id: 'needs_review', label: 'Needs review' },
  { id: 'mismatches', label: 'Mismatches' },
  { id: 'all', label: 'All examples' },
]

export function FilterSelector({
  filter,
  onChange,
}: {
  filter: Filter
  onChange: (filter: Filter) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {FILTERS.map(({ id, label }) => (
        <button
          key={id}
          type="button"
          onClick={() => onChange(id)}
          className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
            filter === id
              ? 'bg-primary text-white shadow'
              : 'bg-card text-ink-soft hover:bg-primary-soft hover:text-primary'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}

const CATEGORY_LABELS: Record<Category, string> = {
  BL_COMPARISON: 'BL comparison',
  SI_REQUEST: 'SI request',
  INVOICE_QUERY: 'Invoice query',
  GENERAL: 'General',
  SPAM: 'Spam',
}

const CATEGORY_STYLES: Record<Category, string> = {
  BL_COMPARISON: 'border-blue-200 bg-primary-soft text-primary',
  SI_REQUEST: 'border-indigo-200 bg-indigo-50 text-indigo-700',
  INVOICE_QUERY: 'border-violet-200 bg-violet-50 text-violet-700',
  GENERAL: 'border-slate-200 bg-slate-100 text-slate-600',
  SPAM: 'border-rose-200 bg-rose-50 text-rose-600',
}

export function CategoryChip({ category }: { category: Category }) {
  return (
    <span className={`rounded-full border px-3 py-0.5 text-xs font-semibold ${CATEGORY_STYLES[category]}`}>
      {CATEGORY_LABELS[category]}
    </span>
  )
}

const STATUS_STYLES: Record<Status, string> = {
  OK: 'border-green-200 bg-ok-soft text-ok',
  MISMATCH: 'border-rose-200 bg-mismatch-soft text-mismatch',
  NEEDS_REVIEW: 'border-amber-200 bg-review-soft text-review',
}

const STATUS_LABELS: Record<Status, string> = {
  OK: 'OK',
  MISMATCH: 'Mismatch',
  NEEDS_REVIEW: 'Needs review',
}

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`rounded-md border px-2.5 py-0.5 text-xs font-bold ${STATUS_STYLES[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  )
}

export function StatCard({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="rounded-xl border border-line bg-card p-5 text-center shadow-sm">
      <div className="text-3xl font-extrabold text-primary">{value}</div>
      <div className="mt-1 text-xs font-bold uppercase tracking-wide text-ink-soft">{label}</div>
    </div>
  )
}
