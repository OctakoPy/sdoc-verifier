export type Category =
  | 'BL_COMPARISON'
  | 'SI_REQUEST'
  | 'INVOICE_QUERY'
  | 'GENERAL'
  | 'SPAM'

export type Status = 'OK' | 'MISMATCH' | 'NEEDS_REVIEW'
export type Filter = 'starter' | 'comparisons' | 'needs_review' | 'mismatches' | 'all'

export interface Overview {
  dataset: { label: string; validation: string }
  total_emails: number
  category_distribution: Record<Category, number>
  status_distribution: Record<Status, number>
  review_reasons: Record<string, number>
  mismatches: { email_count: number; field_counts: Record<string, number> }
}

export interface EmailSummary {
  email_id: string
  subject: string
  category: Category
  status: Status
  review_reason: string | null
  mismatch_fields: string[]
  decided_by: string
  filters: Filter[]
  classification_reason: string
}

export interface EmailList {
  count: number
  emails: EmailSummary[]
}

export interface StoryAttachment {
  path: string
  kind: string
  scanned: boolean
  translated: boolean
  lines: string[]
  anchors: Record<string, number[]>
}

export interface Story {
  email_id: string
  subject: string
  body: string
  classification: { category: Category; confidence: number | null; reason: string }
  attachments: StoryAttachment[]
  comparison: Record<string, { si: string; bl: string; match: boolean | null }> | null
  verdict: {
    status: Status
    review_reason: string | null
    mismatch_fields: string[]
    decided_by: string
    detail: string
  }
  steps: { stage: string; decision: string; detail: string }[]
}

export const FIELD_LABELS: Record<string, string> = {
  shipper: 'Shipper',
  consignee: 'Consignee',
  notify_party: 'Notify Party',
  port_of_loading: 'Port of Loading',
  port_of_discharge: 'Port of Discharge',
  container_count: 'Container Count',
  gross_weight_kg: 'Gross Weight (KG)',
}

export async function api<T>(path: string): Promise<T> {
  const response = await fetch(`/api${path}`)
  if (!response.ok) {
    throw new Error(`${path}: ${response.status}`)
  }
  return (await response.json()) as T
}

const storyCache = new Map<string, Promise<Story>>()

export function fetchStoryCached(emailId: string): Promise<Story> {
  const cached = storyCache.get(emailId)
  if (cached) return cached
  const request = api<Story>(`/emails/${emailId}/story`).catch((error: unknown) => {
    storyCache.delete(emailId)
    throw error
  })
  storyCache.set(emailId, request)
  return request
}
