import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card, CardTitle } from '../components/ui/Card.tsx'
import { EmptyState } from '../components/ui/EmptyState.tsx'
import { DOCUMENT_CATEGORY_LABELS, PROCESSING_STATUS_LABELS } from '../constants/documentEnums.ts'
import { documentFileUrl, getDocumentContent } from '../services/api.ts'
import { getToken } from '../services/session.ts'
import type { DocumentContent } from '../types/entities.ts'

function statusTone(status: string): 'success' | 'accent' | 'danger' | 'neutral' {
  if (status === 'COMPLETED') {
    return 'success'
  }
  if (status === 'FAILED') {
    return 'danger'
  }
  if (status === 'PROCESSING' || status === 'PENDING') {
    return 'accent'
  }
  return 'neutral'
}

export function DocumentDetailPage() {
  const { documentId } = useParams()
  const id = Number(documentId)
  const [content, setContent] = useState<DocumentContent | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    if (!Number.isFinite(id)) {
      setError('Document not found.')
      setLoading(false)
      return
    }
    getDocumentContent(id)
      .then((next) => {
        if (active) {
          setContent(next)
        }
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(caught instanceof Error ? caught.message : 'Could not load document.')
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [id])

  useEffect(() => {
    let objectUrl: string | null = null
    let active = true
    async function loadPreview() {
      if (!content || content.document.file_type !== 'PDF') {
        setPreviewUrl(null)
        return
      }
      try {
        const response = await fetch(documentFileUrl(content.document.id), {
          headers: {
            Authorization: `Bearer ${getToken() ?? ''}`,
          },
        })
        if (!response.ok) {
          return
        }
        const blob = await response.blob()
        objectUrl = URL.createObjectURL(blob)
        if (active) {
          setPreviewUrl(objectUrl)
        }
      } catch {
        if (active) {
          setPreviewUrl(null)
        }
      }
    }
    void loadPreview()
    return () => {
      active = false
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [content])

  if (loading) {
    return (
      <p className="text-sm text-[var(--cp-muted)]" role="status">
        Loading document
      </p>
    )
  }

  if (error || !content) {
    return (
      <section className="space-y-4">
        <Alert>{error ?? 'Document not found.'}</Alert>
        <Link className="text-sm font-semibold text-[var(--cp-brand)] underline-offset-2 hover:underline" to="/documents">
          Back to library
        </Link>
      </section>
    )
  }

  const document = content.document

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link className="text-sm font-semibold text-[var(--cp-brand)] underline-offset-2 hover:underline" to="/documents">
            ← Library
          </Link>
          <h2 className="mt-3 text-xl font-semibold text-[var(--cp-ink)]">{document.title}</h2>
          <p className="mt-2 text-sm text-[var(--cp-muted)]">
            {DOCUMENT_CATEGORY_LABELS[document.category]} · {document.file_type} ·{' '}
            {document.original_filename}
          </p>
        </div>
        <Badge tone={statusTone(document.processing_status)}>
          {PROCESSING_STATUS_LABELS[document.processing_status] ?? document.processing_status}
        </Badge>
      </div>

      {document.description ? (
        <Card>
          <CardTitle>Description</CardTitle>
          <p className="mt-3 text-sm leading-6 text-slate-700">{document.description}</p>
        </Card>
      ) : null}

      {document.processing_error ? <Alert>{document.processing_error}</Alert> : null}

      {document.file_type === 'PDF' ? (
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <CardTitle>PDF preview</CardTitle>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                if (previewUrl) {
                  window.open(previewUrl, '_blank', 'noopener,noreferrer')
                }
              }}
              disabled={!previewUrl}
            >
              Open in tab
            </Button>
          </div>
          {previewUrl ? (
            <iframe title={document.title} src={previewUrl} className="h-[28rem] w-full rounded-xl border border-[var(--cp-border)]" />
          ) : (
            <p className="text-sm text-[var(--cp-muted)]">Preview unavailable for this file.</p>
          )}
        </Card>
      ) : null}

      <Card className="space-y-4">
        <div>
          <CardTitle>Extracted content</CardTitle>
          <p className="mt-1 text-sm text-[var(--cp-muted)]">
            Searchable chunks produced during processing ({content.chunks.length}).
          </p>
        </div>
        {content.chunks.length === 0 ? (
          <EmptyState
            title="No extracted text"
            message="This document has not produced searchable chunks yet."
          />
        ) : (
          <div className="space-y-3">
            {content.chunks.map((chunk) => (
              <div key={chunk.id} className="rounded-xl border border-[var(--cp-border)] px-4 py-3">
                <div className="mb-2 flex flex-wrap gap-2">
                  <Badge tone="neutral">Chunk {chunk.chunk_index + 1}</Badge>
                  {chunk.page_number ? <Badge tone="accent">Page {chunk.page_number}</Badge> : null}
                </div>
                <p className="text-sm leading-6 text-slate-700 whitespace-pre-wrap">{chunk.content}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </section>
  )
}
