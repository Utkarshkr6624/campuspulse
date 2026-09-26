import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { DragEvent, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card, CardTitle } from '../components/ui/Card.tsx'
import { EmptyState } from '../components/ui/EmptyState.tsx'
import { SelectField, TextAreaField, TextField } from '../components/ui/Field.tsx'
import { Modal } from '../components/ui/Modal.tsx'
import {
  DOCUMENT_CATEGORIES,
  DOCUMENT_CATEGORY_LABELS,
  PROCESSING_STATUS_LABELS,
} from '../constants/documentEnums.ts'
import type { DocumentCategoryOption } from '../constants/documentEnums.ts'
import { useAuth } from '../hooks/useAuth.tsx'
import { deleteDocument, getDocuments, searchDocuments, uploadDocument } from '../services/api.ts'
import { ApiError } from '../services/http.ts'
import type { CampusDocument, DocumentSearchHit } from '../types/entities.ts'

function formatBytes(size: number): string {
  if (size < 1024) {
    return `${size} B`
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function statusTone(status: string): 'success' | 'accent' | 'danger' | 'neutral' | 'brand' {
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

function highlightSnippet(snippet: string, query: string): string {
  const tokens = query
    .toLowerCase()
    .split(/\s+/)
    .filter((token) => token.length >= 2)
  if (!tokens.length) {
    return snippet
  }
  const pattern = new RegExp(`(${tokens.map((token) => token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi')
  return snippet.replace(pattern, '«$1»')
}

export function DocumentsPage() {
  const { student } = useAuth()
  const isAdmin = student?.role === 'ADMIN'
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [documents, setDocuments] = useState<CampusDocument[]>([])
  const [results, setResults] = useState<DocumentSearchHit[]>([])
  const [query, setQuery] = useState('')
  const [activeQuery, setActiveQuery] = useState('')
  const [category, setCategory] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)

  const [uploaderOpen, setUploaderOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [uploadCategory, setUploadCategory] = useState<DocumentCategoryOption>('GENERAL')
  const [file, setFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const next = await getDocuments(category ? { category: category as DocumentCategoryOption } : {})
      setDocuments(next)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load documents.')
    } finally {
      setLoading(false)
    }
  }, [category])

  useEffect(() => {
    void load()
  }, [load])

  async function handleSearch(event: FormEvent) {
    event.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) {
      setActiveQuery('')
      setResults([])
      return
    }
    setSearching(true)
    setError(null)
    try {
      const response = await searchDocuments(trimmed)
      setActiveQuery(trimmed)
      setResults(response.results)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Search failed.')
    } finally {
      setSearching(false)
    }
  }

  function openUploader() {
    setUploadError(null)
    setUploadSuccess(null)
    setTitle('')
    setDescription('')
    setUploadCategory('GENERAL')
    setFile(null)
    setUploaderOpen(true)
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragOver(false)
    const next = event.dataTransfer.files?.[0]
    if (next) {
      setFile(next)
      if (!title) {
        setTitle(next.name.replace(/\.[^.]+$/, ''))
      }
    }
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault()
    if (!file) {
      setUploadError('Choose a PDF, TXT, or DOCX file.')
      return
    }
    setUploading(true)
    setUploadError(null)
    setUploadSuccess(null)
    try {
      const created = await uploadDocument({
        title: title.trim(),
        category: uploadCategory,
        description: description.trim() || undefined,
        file,
      })
      setUploadSuccess(
        created.processing_status === 'COMPLETED'
          ? 'Document uploaded and processed.'
          : created.processing_status === 'FAILED'
            ? `Uploaded, but processing failed: ${created.processing_error ?? 'unknown error'}`
            : 'Document uploaded and is processing.',
      )
      setUploaderOpen(false)
      await load()
    } catch (caught) {
      setUploadError(caught instanceof ApiError ? caught.message : 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  async function handleDelete(document: CampusDocument) {
    const confirmed = window.confirm(`Delete “${document.title}”?`)
    if (!confirmed) {
      return
    }
    try {
      await deleteDocument(document.id)
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not delete document.')
    }
  }

  const showingSearch = activeQuery.length > 0

  const filteredLibrary = useMemo(() => documents, [documents])

  return (
    <section className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-[var(--cp-ink)]">University library</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">
            Search regulations, circulars, and handbooks. Keyword search over extracted document text.
          </p>
        </div>
        {isAdmin ? <Button onClick={openUploader}>Upload document</Button> : null}
      </div>

      <Card>
        <form className="flex flex-col gap-3 sm:flex-row" onSubmit={(event) => void handleSearch(event)}>
          <TextField
            label="Search university documents"
            name="q"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder='Try “minimum attendance”'
            className="sm:flex-1"
          />
          <div className="flex items-end gap-2">
            <Button type="submit" disabled={searching}>
              {searching ? 'Searching' : 'Search'}
            </Button>
            {showingSearch ? (
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setActiveQuery('')
                  setResults([])
                  setQuery('')
                }}
              >
                Clear
              </Button>
            ) : null}
          </div>
        </form>
      </Card>

      {error ? <Alert>{error}</Alert> : null}
      {uploadSuccess ? <Alert>{uploadSuccess}</Alert> : null}

      {showingSearch ? (
        <section className="space-y-4">
          <div>
            <h3 className="text-base font-semibold text-[var(--cp-ink)]">Search results</h3>
            <p className="mt-1 text-sm text-[var(--cp-muted)]">
              {results.length} match{results.length === 1 ? '' : 'es'} for “{activeQuery}”
            </p>
          </div>
          {results.length === 0 ? (
            <EmptyState
              title="No matching passages"
              message="Try different keywords, or browse the library below."
            />
          ) : (
            <div className="space-y-3">
              {results.map((hit) => (
                <Card key={`${hit.document_id}-${hit.page_number}-${hit.snippet.slice(0, 24)}`}>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-[var(--cp-ink)]">{hit.title}</p>
                    <Badge tone="brand">{DOCUMENT_CATEGORY_LABELS[hit.category]}</Badge>
                    <Badge tone="neutral">{hit.file_type}</Badge>
                    {hit.page_number ? <Badge tone="accent">Page {hit.page_number}</Badge> : null}
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-700">
                    {highlightSnippet(hit.snippet, activeQuery)
                      .split(/(«[^»]+»)/g)
                      .map((part, index) =>
                        part.startsWith('«') && part.endsWith('»') ? (
                          <mark
                            key={`${hit.document_id}-${index}`}
                            className="rounded bg-[color-mix(in_srgb,var(--cp-accent)_35%,white)] px-0.5"
                          >
                            {part.slice(1, -1)}
                          </mark>
                        ) : (
                          <span key={`${hit.document_id}-${index}`}>{part}</span>
                        ),
                      )}
                  </p>
                  <div className="mt-4">
                    <Link
                      className="text-sm font-semibold text-[var(--cp-brand)] underline-offset-2 hover:underline"
                      to={`/documents/${hit.document_id}`}
                    >
                      Open document
                    </Link>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </section>
      ) : null}

      <section className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h3 className="text-base font-semibold text-[var(--cp-ink)]">Document library</h3>
            <p className="mt-1 text-sm text-[var(--cp-muted)]">Browse uploaded university materials.</p>
          </div>
          <SelectField
            label="Category"
            name="category"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="">All categories</option>
            {DOCUMENT_CATEGORIES.map((item) => (
              <option key={item} value={item}>
                {DOCUMENT_CATEGORY_LABELS[item]}
              </option>
            ))}
          </SelectField>
        </div>

        {loading ? (
          <p className="text-sm text-[var(--cp-muted)]" role="status">
            Loading documents
          </p>
        ) : null}

        {!loading && filteredLibrary.length === 0 ? (
          <EmptyState
            title="No documents yet"
            message={
              isAdmin
                ? 'Upload a PDF, TXT, or DOCX handbook to start the knowledge library.'
                : 'An administrator has not uploaded university documents yet.'
            }
            actionLabel={isAdmin ? 'Upload document' : undefined}
            onAction={isAdmin ? openUploader : undefined}
          />
        ) : null}

        {!loading && filteredLibrary.length > 0 ? (
          <div className="grid gap-3 md:grid-cols-2">
            {filteredLibrary.map((document) => (
              <Card key={document.id} className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-[var(--cp-ink)]">{document.title}</p>
                    <p className="mt-1 text-xs text-[var(--cp-muted)]">
                      {DOCUMENT_CATEGORY_LABELS[document.category]} · {document.file_type} ·{' '}
                      {formatBytes(document.file_size)}
                    </p>
                  </div>
                  <Badge tone={statusTone(document.processing_status)}>
                    {PROCESSING_STATUS_LABELS[document.processing_status] ?? document.processing_status}
                  </Badge>
                </div>
                <p className="text-xs text-[var(--cp-muted)]">Uploaded {formatDate(document.created_at)}</p>
                {document.processing_error ? (
                  <p className="text-xs text-red-700">{document.processing_error}</p>
                ) : null}
                <div className="flex flex-wrap gap-2">
                  <Link
                    className="inline-flex items-center rounded-xl bg-[var(--cp-brand)] px-3 py-1.5 text-sm font-semibold text-white"
                    to={`/documents/${document.id}`}
                  >
                    Open
                  </Link>
                  {isAdmin ? (
                    <Button size="sm" variant="ghost" onClick={() => void handleDelete(document)}>
                      Delete
                    </Button>
                  ) : null}
                </div>
              </Card>
            ))}
          </div>
        ) : null}
      </section>

      <Modal
        open={uploaderOpen}
        title="Upload university document"
        onClose={() => setUploaderOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setUploaderOpen(false)} disabled={uploading}>
              Cancel
            </Button>
            <Button type="submit" form="document-upload-form" disabled={uploading}>
              {uploading ? 'Uploading & processing' : 'Upload'}
            </Button>
          </>
        }
      >
        <form id="document-upload-form" className="space-y-4" onSubmit={(event) => void handleUpload(event)}>
          <TextField
            label="Title"
            name="title"
            required
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
          <SelectField
            label="Category"
            name="category"
            value={uploadCategory}
            onChange={(event) => setUploadCategory(event.target.value as DocumentCategoryOption)}
          >
            {DOCUMENT_CATEGORIES.map((item) => (
              <option key={item} value={item}>
                {DOCUMENT_CATEGORY_LABELS[item]}
              </option>
            ))}
          </SelectField>
          <TextAreaField
            label="Description"
            name="description"
            rows={3}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          <div
            onDragOver={(event) => {
              event.preventDefault()
              setDragOver(true)
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            className={`rounded-xl border border-dashed px-4 py-8 text-center transition ${
              dragOver
                ? 'border-[var(--cp-brand)] bg-[color-mix(in_srgb,var(--cp-brand)_6%,white)]'
                : 'border-[var(--cp-border)] bg-slate-50'
            }`}
          >
            <CardTitle>Drop a file here</CardTitle>
            <p className="mt-2 text-sm text-[var(--cp-muted)]">PDF, TXT, or DOCX · max 10 MB</p>
            <div className="mt-4">
              <Button type="button" variant="secondary" size="sm" onClick={() => fileInputRef.current?.click()}>
                Choose file
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.docx,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                className="hidden"
                onChange={(event) => {
                  const next = event.target.files?.[0] ?? null
                  setFile(next)
                  if (next && !title) {
                    setTitle(next.name.replace(/\.[^.]+$/, ''))
                  }
                }}
              />
            </div>
            {file ? (
              <p className="mt-3 text-sm font-medium text-[var(--cp-ink)]">
                {file.name} · {formatBytes(file.size)}
              </p>
            ) : null}
          </div>
          {uploadError ? <Alert>{uploadError}</Alert> : null}
          {uploading ? (
            <p className="text-sm text-[var(--cp-muted)]" role="status">
              Uploading and extracting text…
            </p>
          ) : null}
        </form>
      </Modal>
    </section>
  )
}
