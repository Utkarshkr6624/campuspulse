import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card, CardTitle } from '../components/ui/Card.tsx'
import { Icon } from '../components/ui/Icon.tsx'
import {
  deleteAiConversation,
  getAiConversation,
  getAiConversations,
  sendAiChat,
} from '../services/api.ts'
import { ApiError } from '../services/http.ts'
import type { ChatMessage, ChatSource, ConversationSummary } from '../types/entities.ts'

const SUGGESTIONS = [
  { title: 'Analyze my semester', prompt: 'How am I doing this semester?', icon: 'chart' as const },
  { title: 'Review my GPA', prompt: 'What is my current GPA and CGPA?', icon: 'grid' as const },
  { title: 'Compare semesters', prompt: 'Compare my semester performance trend.', icon: 'calendar' as const },
  { title: 'Check attendance risk', prompt: 'Where is my attendance below the configured threshold?', icon: 'check' as const },
  { title: 'Plan my focus', prompt: 'Which subjects should I focus on based on my current records?', icon: 'spark' as const },
  { title: 'See upcoming exams', prompt: 'What exams are coming up?', icon: 'file' as const },
]

type DisplayMessage = {
  id: string
  role: 'USER' | 'ASSISTANT'
  content: string
  sources: ChatSource[]
  tools_used: string[]
  grounding: string[]
  created_at?: string
}

function toDisplay(message: ChatMessage): DisplayMessage {
  return {
    id: String(message.id),
    role: message.role,
    content: message.content,
    sources: message.sources,
    tools_used: message.tools_used,
    grounding: message.grounding,
    created_at: message.created_at,
  }
}

export function AssistantPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [input, setInput] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loadingList, setLoadingList] = useState(true)
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const handledContextKey = useRef<string | null>(null)

  useEffect(() => {
    void refreshConversations()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, sending])

  async function refreshConversations() {
    setLoadingList(true)
    try {
      const list = await getAiConversations()
      setConversations(list)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load conversations.')
    } finally {
      setLoadingList(false)
    }
  }

  async function openConversation(id: number) {
    setError(null)
    try {
      const detail = await getAiConversation(id)
      setConversationId(detail.id)
      setMessages(detail.messages.map(toDisplay))
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not open conversation.')
    }
  }

  function startNewConversation() {
    setConversationId(null)
    setMessages([])
    setError(null)
    setInput('')
  }

  async function clearCurrent() {
    if (conversationId === null) {
      startNewConversation()
      return
    }
    try {
      await deleteAiConversation(conversationId)
      startNewConversation()
      await refreshConversations()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not clear conversation.')
    }
  }

  const submitMessage = useCallback(async (raw: string) => {
    const text = raw.trim()
    if (!text || sending) {
      return
    }
    setError(null)
    setSending(true)
    setInput('')
    const optimisticId = `local-${Date.now()}`
    setMessages((prev) => [
      ...prev,
      {
        id: optimisticId,
        role: 'USER',
        content: text,
        sources: [],
        tools_used: [],
        grounding: [],
        created_at: new Date().toISOString(),
      },
    ])
    try {
      const response = await sendAiChat(text, conversationId)
      setConversationId(response.conversation_id)
      setMessages((prev) => [
        ...prev.filter((item) => item.id !== optimisticId),
        {
          id: `${optimisticId}-user`,
          role: 'USER',
          content: text,
          sources: [],
          tools_used: [],
          grounding: [],
          created_at: new Date().toISOString(),
        },
        {
          id: String(response.message_id),
          role: 'ASSISTANT',
          content: response.answer,
          sources: response.sources,
          tools_used: response.tools_used,
          grounding: response.grounding,
          created_at: new Date().toISOString(),
        },
      ])
      await refreshConversations()
    } catch (caught) {
      setMessages((prev) => prev.filter((item) => item.id !== optimisticId))
      setInput(text)
      const message =
        caught instanceof ApiError && caught.status >= 500
          ? 'CampusPulse AI is temporarily unavailable.'
          : caught instanceof Error
            ? caught.message
            : 'CampusPulse AI is temporarily unavailable.'
      setError(message)
    } finally {
      setSending(false)
    }
  }, [conversationId, sending])

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void submitMessage(input)
  }

  useEffect(() => {
    const state = location.state as { prompt?: string } | null
    const prompt = state?.prompt?.trim()
    if (!prompt || handledContextKey.current === location.key) return
    handledContextKey.current = location.key
    navigate('/assistant', { replace: true, state: null })
    void submitMessage(prompt)
  }, [location.key, location.state, navigate, submitMessage])

  return (
    <section className="space-y-5" aria-labelledby="assistant-heading">
      <div className="flex flex-col gap-4 rounded-[1.35rem] border border-[var(--cp-border)] bg-white p-5 sm:flex-row sm:items-end sm:justify-between sm:p-7">
        <div className="max-w-2xl">
          <div className="flex flex-wrap items-center gap-2"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--cp-brand-wash)] text-[var(--cp-brand)]"><Icon name="spark" className="h-5 w-5" /></span><Badge tone="brand">Deterministic · no LLM connected</Badge></div>
          <h2 id="assistant-heading" className="mt-4 text-2xl font-semibold tracking-[-0.045em] text-[var(--cp-ink)] sm:text-3xl">CampusPulse Intelligence</h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-[var(--cp-muted)]">Understand your academic life. Answers are assembled from your authenticated academic records and available university documents.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={startNewConversation}><Icon name="plus" className="h-4 w-4" />New conversation</Button>
          <Button variant="ghost" onClick={() => void clearCurrent()} disabled={messages.length === 0}>Clear</Button>
        </div>
      </div>

      {error ? <Alert>{error}</Alert> : null}

      <div className="grid items-start gap-5 xl:grid-cols-[16rem_minmax(0,1fr)]">
        <Card className="order-2 space-y-4 xl:order-1">
          <div className="flex items-center justify-between gap-2"><CardTitle>Conversation history</CardTitle><Badge>{conversations.length}</Badge></div>
          {loadingList ? <p className="text-sm text-[var(--cp-muted)]" role="status">Loading history…</p> : null}
          {!loadingList && conversations.length === 0 ? <p className="rounded-xl bg-[var(--cp-surface-raised)] px-3 py-4 text-xs leading-5 text-[var(--cp-muted)]">Your conversations will appear here.</p> : null}
          <ul className="max-h-[32rem] space-y-1.5 overflow-y-auto">
            {conversations.map((item) => (
              <li key={item.id}>
                <button type="button" aria-current={conversationId === item.id ? 'page' : undefined} onClick={() => void openConversation(item.id)} className={`w-full rounded-[0.75rem] border px-3 py-3 text-left transition ${conversationId === item.id ? 'border-[#c7d9cc] bg-[var(--cp-brand-wash)]' : 'border-transparent hover:border-[var(--cp-border)] hover:bg-[var(--cp-surface-raised)]'}`}>
                  <span className="line-clamp-2 block text-xs font-semibold leading-5 text-[var(--cp-ink)]">{item.title}</span>
                  <span className="mt-1.5 block text-[0.68rem] text-[var(--cp-muted)]">{item.message_count} messages</span>
                </button>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="order-1 flex min-h-[36rem] flex-col overflow-hidden p-0 xl:order-2">
          <div className="flex min-h-12 items-center justify-between gap-3 border-b border-[var(--cp-border)] px-4 py-3 sm:px-6">
            <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[var(--cp-success)]" /><p className="text-xs font-semibold text-[var(--cp-ink)]">Grounded responses</p></div>
            <p className="text-[0.68rem] text-[var(--cp-muted)]">Your account data stays with CampusPulse</p>
          </div>
          <div className="flex-1 space-y-4 overflow-y-auto px-4 py-5 sm:px-6" aria-live="polite">
            {messages.length === 0 ? (
              <div className="mx-auto flex min-h-[27rem] max-w-3xl flex-col justify-center py-5">
                <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--cp-brand)] text-[var(--cp-accent)]"><Icon name="spark" className="h-6 w-6" /></div>
                <p className="cp-kicker">Academic guide</p>
                <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-[var(--cp-ink)]">What would you like to understand?</h3>
                <p className="mt-2 max-w-xl text-sm leading-6 text-[var(--cp-muted)]">Choose a starting point or ask a question in your own words. Numerical answers come from CampusPulse calculation services.</p>
                <div className="mt-6 grid gap-2 sm:grid-cols-2">
                  {SUGGESTIONS.map((suggestion) => (
                    <button key={suggestion.title} type="button" onClick={() => void submitMessage(suggestion.prompt)} disabled={sending} className="group flex min-h-[4.1rem] items-center gap-3 rounded-[0.85rem] border border-[var(--cp-border)] bg-white px-3.5 py-3 text-left transition hover:border-[#bed1c3] hover:bg-[var(--cp-surface-raised)] focus-visible:outline-2 focus-visible:outline-offset-2">
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--cp-brand-wash)] text-[var(--cp-brand)]"><Icon name={suggestion.icon} className="h-4 w-4" /></span>
                      <span className="text-xs font-semibold text-[var(--cp-ink)]">{suggestion.title}</span>
                      <Icon name="arrow" className="ml-auto h-4 w-4 text-[#9ba89f] transition group-hover:translate-x-0.5 group-hover:text-[var(--cp-brand)]" />
                    </button>
                  ))}
                </div>
              </div>
            ) : messages.map((message) => (
              <article key={message.id} className={`flex gap-3 ${message.role === 'USER' ? 'justify-end' : 'justify-start'}`}>
                {message.role === 'ASSISTANT' ? <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[var(--cp-brand)] text-[var(--cp-accent)]"><Icon name="spark" className="h-4 w-4" /></span> : null}
                <div className={`max-w-[88%] rounded-[1rem] px-4 py-3 sm:max-w-[80%] ${message.role === 'USER' ? 'rounded-br-sm bg-[var(--cp-brand)] text-white' : 'rounded-tl-sm border border-[var(--cp-border)] bg-[var(--cp-surface-raised)] text-[var(--cp-ink)]'}`}>
                  <div className="flex items-center gap-2"><p className="text-[0.65rem] font-bold uppercase tracking-[0.1em] opacity-65">{message.role === 'USER' ? 'You' : 'CampusPulse · grounded response'}</p>{message.created_at ? <time className="text-[0.62rem] opacity-55" dateTime={message.created_at}>{new Date(message.created_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</time> : null}</div>
                  <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6">{message.content}</p>
                  {message.role === 'ASSISTANT' && message.grounding.length ? <div className="mt-3 flex flex-wrap gap-1.5">{message.grounding.map((item) => <Badge key={item} tone="neutral">{item.replaceAll('_', ' ')}</Badge>)}</div> : null}
                  {message.role === 'ASSISTANT' && message.sources.length ? <div className="mt-4 rounded-[0.75rem] border border-[var(--cp-border)] bg-white px-3.5 py-3"><p className="text-[0.65rem] font-bold uppercase tracking-[0.1em] text-[var(--cp-muted)]">Document sources</p><ul className="mt-2 space-y-3">{message.sources.map((source) => <li key={`${source.document_id}-${source.page_number}-${source.title}`}><Link className="text-xs font-semibold text-[var(--cp-brand)] hover:underline" to={`/documents/${source.document_id}`}>{source.title}{source.page_number ? ` · Page ${source.page_number}` : ''}</Link>{source.snippet ? <p className="mt-1 text-xs leading-5 text-[var(--cp-muted)]">{source.snippet}</p> : null}</li>)}</ul></div> : null}
                </div>
                {message.role === 'USER' ? <span aria-hidden="true" className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#e7ece8] text-[0.65rem] font-bold text-[var(--cp-brand)]">YOU</span> : null}
              </article>
            ))}
            {sending ? <div className="flex items-center gap-3" role="status"><span className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--cp-brand-wash)] text-[var(--cp-brand)]"><Icon name="spark" className="h-4 w-4" /></span><p className="text-xs text-[var(--cp-muted)]">Checking your academic records…</p></div> : null}
            <div ref={bottomRef} />
          </div>

          <form className="border-t border-[var(--cp-border)] bg-[var(--cp-surface-raised)] p-3 sm:p-4" onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor="ai-message">Ask CampusPulse</label>
            <textarea id="ai-message" rows={2} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void submitMessage(input) } }} placeholder="Ask about GPA, marks, attendance, deadlines…" className="w-full resize-y rounded-[0.8rem] border border-[var(--cp-border)] bg-white px-3.5 py-3 text-sm leading-6 text-[var(--cp-ink)] placeholder:text-[var(--cp-muted)] focus:border-[var(--cp-brand)] focus:ring-4 focus:ring-[color-mix(in_srgb,var(--cp-brand)_8%,transparent)]" disabled={sending} />
            <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
              <p className="text-[0.68rem] text-[var(--cp-muted)]">Rule-based responses · no external LLM is connected <span className="hidden sm:inline">· Shift + Enter for a new line</span></p>
              <div className="flex gap-2">{error ? <Button type="button" variant="secondary" size="sm" disabled={sending || !input.trim()} onClick={() => void submitMessage(input)}>Retry</Button> : null}<Button type="submit" size="sm" disabled={sending || !input.trim()}>{sending ? 'Working…' : 'Send'}<Icon name="arrow" className="h-4 w-4" /></Button></div>
            </div>
          </form>
        </Card>
      </div>
    </section>
  )
}
