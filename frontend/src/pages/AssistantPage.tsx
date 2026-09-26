import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card, CardTitle } from '../components/ui/Card.tsx'
import { EmptyState } from '../components/ui/EmptyState.tsx'
import {
  deleteAiConversation,
  getAiConversation,
  getAiConversations,
  sendAiChat,
} from '../services/api.ts'
import { ApiError } from '../services/http.ts'
import type { ChatMessage, ChatSource, ConversationSummary } from '../types/entities.ts'

const SUGGESTIONS = [
  'What is my current GPA?',
  'How is my attendance?',
  'What exams are coming up?',
  'Which subjects need attention?',
  'What does the attendance policy say?',
  'Summarize my academic performance.',
]

type DisplayMessage = {
  id: string
  role: 'USER' | 'ASSISTANT'
  content: string
  sources: ChatSource[]
  tools_used: string[]
  grounding: string[]
}

function toDisplay(message: ChatMessage): DisplayMessage {
  return {
    id: String(message.id),
    role: message.role,
    content: message.content,
    sources: message.sources,
    tools_used: message.tools_used,
    grounding: message.grounding,
  }
}

export function AssistantPage() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [input, setInput] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loadingList, setLoadingList] = useState(true)
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

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

  async function submitMessage(raw: string) {
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
        },
        {
          id: String(response.message_id),
          role: 'ASSISTANT',
          content: response.answer,
          sources: response.sources,
          tools_used: response.tools_used,
          grounding: response.grounding,
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
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void submitMessage(input)
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-[var(--cp-ink)]">CampusPulse AI</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">
            Your university assistant — grounded in your CampusPulse records and official documents.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={startNewConversation}>
            New chat
          </Button>
          <Button variant="ghost" onClick={() => void clearCurrent()} disabled={messages.length === 0}>
            Clear
          </Button>
        </div>
      </div>

      {error ? <Alert>{error}</Alert> : null}

      <div className="grid gap-6 xl:grid-cols-[0.85fr_1.6fr]">
        <Card className="space-y-3">
          <CardTitle>Conversations</CardTitle>
          {loadingList ? (
            <p className="text-sm text-[var(--cp-muted)]" role="status">
              Loading conversations
            </p>
          ) : null}
          {!loadingList && conversations.length === 0 ? (
            <p className="text-sm text-[var(--cp-muted)]">No chats yet. Ask your first question.</p>
          ) : null}
          <ul className="space-y-2">
            {conversations.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => void openConversation(item.id)}
                  className={`w-full rounded-xl border px-3 py-2.5 text-left text-sm transition ${
                    conversationId === item.id
                      ? 'border-[var(--cp-brand)] bg-[color-mix(in_srgb,var(--cp-brand)_8%,white)]'
                      : 'border-[var(--cp-border)] hover:bg-slate-50'
                  }`}
                >
                  <span className="line-clamp-2 font-medium text-[var(--cp-ink)]">{item.title}</span>
                  <span className="mt-1 block text-xs text-[var(--cp-muted)]">
                    {item.message_count} messages
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="flex min-h-[32rem] flex-col">
          <div className="flex-1 space-y-4 overflow-y-auto pr-1">
            {messages.length === 0 ? (
              <EmptyState
                title="Ask CampusPulse"
                message="Questions about your GPA, attendance, exams, assignments, or university policies are answered from real CampusPulse data and documents."
              >
                <div className="mt-5 flex flex-wrap gap-2">
                  {SUGGESTIONS.map((suggestion) => (
                    <Button
                      key={suggestion}
                      size="sm"
                      variant="secondary"
                      onClick={() => void submitMessage(suggestion)}
                      disabled={sending}
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </EmptyState>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`rounded-2xl px-4 py-3 ${
                    message.role === 'USER'
                      ? 'ml-6 bg-[var(--cp-brand)] text-white'
                      : 'mr-6 border border-[var(--cp-border)] bg-white'
                  }`}
                >
                  <p className="text-xs font-semibold tracking-wide uppercase opacity-70">
                    {message.role === 'USER' ? 'You' : 'CampusPulse AI'}
                  </p>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{message.content}</p>
                  {message.role === 'ASSISTANT' && message.grounding.length > 0 ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {message.grounding.map((item) => (
                        <Badge key={item} tone="neutral">
                          {item.replaceAll('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  ) : null}
                  {message.role === 'ASSISTANT' && message.sources.length > 0 ? (
                    <div className="mt-4 rounded-xl border border-[var(--cp-border)] bg-slate-50 px-3 py-3">
                      <p className="text-xs font-semibold tracking-wide text-[var(--cp-muted)] uppercase">
                        Sources
                      </p>
                      <ul className="mt-2 space-y-2">
                        {message.sources.map((source) => (
                          <li key={`${source.document_id}-${source.page_number}-${source.title}`}>
                            <Link
                              className="text-sm font-semibold text-[var(--cp-brand)] underline-offset-2 hover:underline"
                              to={`/documents/${source.document_id}`}
                            >
                              {source.title}
                              {source.page_number ? ` · Page ${source.page_number}` : ''}
                            </Link>
                            {source.snippet ? (
                              <p className="mt-1 text-xs leading-5 text-[var(--cp-muted)]">
                                {source.snippet}
                              </p>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </div>
              ))
            )}
            {sending ? (
              <p className="text-sm text-[var(--cp-muted)]" role="status">
                CampusPulse AI is thinking…
              </p>
            ) : null}
            <div ref={bottomRef} />
          </div>

          <form className="mt-4 flex flex-col gap-3 border-t border-[var(--cp-border)] pt-4" onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor="ai-message">
              Ask CampusPulse
            </label>
            <textarea
              id="ai-message"
              rows={3}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask CampusPulse…"
              className="w-full rounded-xl border border-[var(--cp-border)] bg-white px-3.5 py-2.5 text-sm text-[var(--cp-ink)] outline-none focus:border-[var(--cp-brand)]"
              disabled={sending}
            />
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs text-[var(--cp-muted)]">
                Answers use your authenticated data and university documents only.
              </p>
              <div className="flex gap-2">
                {error ? (
                  <Button
                    type="button"
                    variant="secondary"
                    disabled={sending || !input.trim()}
                    onClick={() => void submitMessage(input)}
                  >
                    Retry
                  </Button>
                ) : null}
                <Button type="submit" disabled={sending || !input.trim()}>
                  {sending ? 'Sending' : 'Send'}
                </Button>
              </div>
            </div>
          </form>
        </Card>
      </div>
    </section>
  )
}
