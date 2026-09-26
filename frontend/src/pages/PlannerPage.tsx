import { useCallback, useEffect, useMemo, useState } from 'react'
import { Alert } from '../components/ui/Alert.tsx'
import { Badge } from '../components/ui/Badge.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card, CardTitle } from '../components/ui/Card.tsx'
import { EmptyState } from '../components/ui/EmptyState.tsx'
import { Modal } from '../components/ui/Modal.tsx'
import { getAssignments, getExams } from '../services/api.ts'
import type { PlannerEvent } from '../types/entities.ts'
import { buildCalendarEvents, buildUpcomingEvents } from '../utils/plannerEvents.ts'

function startOfMonth(year: number, month: number): Date {
  return new Date(year, month, 1)
}

function daysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate()
}

function toIsoDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatLongDate(value: string): string {
  return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

function urgencyTone(urgency: PlannerEvent['urgency']): 'danger' | 'accent' | 'brand' | 'success' | 'neutral' {
  if (urgency === 'overdue') {
    return 'danger'
  }
  if (urgency === 'today') {
    return 'accent'
  }
  if (urgency === 'soon') {
    return 'brand'
  }
  if (urgency === 'done') {
    return 'success'
  }
  return 'neutral'
}

export function PlannerPage() {
  const today = useMemo(() => new Date(), [])
  const [cursor, setCursor] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1))
  const [events, setEvents] = useState<PlannerEvent[]>([])
  const [upcoming, setUpcoming] = useState<PlannerEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [selectedEvent, setSelectedEvent] = useState<PlannerEvent | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [exams, assignments] = await Promise.all([getExams(), getAssignments()])
      setEvents(buildCalendarEvents(exams, assignments))
      setUpcoming(buildUpcomingEvents(exams, assignments).slice(0, 8))
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load planner.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const year = cursor.getFullYear()
  const month = cursor.getMonth()
  const monthLabel = cursor.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
  const firstWeekday = startOfMonth(year, month).getDay()
  const totalDays = daysInMonth(year, month)
  const todayIso = toIsoDate(today)

  const eventsByDate = useMemo(() => {
    const map = new Map<string, PlannerEvent[]>()
    for (const event of events) {
      const list = map.get(event.date) ?? []
      list.push(event)
      map.set(event.date, list)
    }
    return map
  }, [events])

  const dayCells = useMemo(() => {
    const cells: Array<{ date: string | null; day: number | null }> = []
    for (let index = 0; index < firstWeekday; index += 1) {
      cells.push({ date: null, day: null })
    }
    for (let day = 1; day <= totalDays; day += 1) {
      const date = new Date(year, month, day)
      cells.push({ date: toIsoDate(date), day })
    }
    while (cells.length % 7 !== 0) {
      cells.push({ date: null, day: null })
    }
    return cells
  }, [firstWeekday, month, totalDays, year])

  const selectedDayEvents = selectedDate ? (eventsByDate.get(selectedDate) ?? []) : []

  return (
    <section className="space-y-8">
      <div>
        <h2 className="text-base font-semibold text-[var(--cp-ink)]">Academic planner</h2>
        <p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--cp-muted)]">
          A month view of exams and assignment deadlines from your real schedule.
        </p>
      </div>

      {error ? <Alert>{error}</Alert> : null}
      {loading ? (
        <p className="text-sm text-[var(--cp-muted)]" role="status">
          Loading planner
        </p>
      ) : null}

      {!loading ? (
        <div className="grid gap-6 xl:grid-cols-[1.7fr_0.9fr]">
          <Card className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <CardTitle>{monthLabel}</CardTitle>
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setCursor(new Date(year, month - 1, 1))}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setCursor(new Date(today.getFullYear(), today.getMonth(), 1))}
                >
                  Today
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setCursor(new Date(year, month + 1, 1))}
                >
                  Next
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-7 gap-1 text-center text-xs font-semibold text-[var(--cp-muted)]">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((label) => (
                <div key={label} className="py-2">
                  {label}
                </div>
              ))}
            </div>

            <div className="grid grid-cols-7 gap-1">
              {dayCells.map((cell, index) => {
                if (!cell.date) {
                  return <div key={`empty-${index}`} className="min-h-24 rounded-xl bg-slate-50/60" />
                }
                const dayEvents = eventsByDate.get(cell.date) ?? []
                const isToday = cell.date === todayIso
                const isSelected = cell.date === selectedDate
                return (
                  <button
                    key={cell.date}
                    type="button"
                    onClick={() => setSelectedDate(cell.date)}
                    className={`min-h-24 rounded-xl border p-2 text-left transition ${
                      isSelected
                        ? 'border-[var(--cp-brand)] bg-[color-mix(in_srgb,var(--cp-brand)_8%,white)]'
                        : isToday
                          ? 'border-[var(--cp-accent)] bg-white'
                          : 'border-[var(--cp-border)] bg-white hover:bg-slate-50'
                    }`}
                  >
                    <span className="text-xs font-semibold text-[var(--cp-ink)]">{cell.day}</span>
                    <div className="mt-2 space-y-1">
                      {dayEvents.slice(0, 2).map((event) => (
                        <button
                          key={event.id}
                          type="button"
                          className="block w-full truncate rounded-md bg-slate-100 px-1.5 py-0.5 text-left text-[10px] font-medium text-slate-700"
                          onClick={(clickEvent) => {
                            clickEvent.stopPropagation()
                            setSelectedEvent(event)
                          }}
                        >
                          {event.kind === 'exam' ? 'Exam' : 'Due'} · {event.title}
                        </button>
                      ))}
                      {dayEvents.length > 2 ? (
                        <p className="text-[10px] text-[var(--cp-muted)]">+{dayEvents.length - 2} more</p>
                      ) : null}
                    </div>
                  </button>
                )
              })}
            </div>
          </Card>

          <div className="space-y-4">
            <Card className="space-y-3">
              <CardTitle>{selectedDate ? formatLongDate(selectedDate) : 'Day details'}</CardTitle>
              {!selectedDate ? (
                <p className="text-sm text-[var(--cp-muted)]">Select a day to inspect exams and deadlines.</p>
              ) : selectedDayEvents.length === 0 ? (
                <p className="text-sm text-[var(--cp-muted)]">No academic events on this day.</p>
              ) : (
                <ul className="space-y-3">
                  {selectedDayEvents.map((event) => (
                    <li key={event.id}>
                      <button
                        type="button"
                        className="w-full rounded-xl border border-[var(--cp-border)] px-3 py-3 text-left transition hover:bg-slate-50"
                        onClick={() => setSelectedEvent(event)}
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge tone={event.kind === 'exam' ? 'brand' : 'accent'}>
                            {event.kind === 'exam' ? 'Exam' : 'Assignment'}
                          </Badge>
                          <Badge tone={urgencyTone(event.urgency)}>{event.urgency}</Badge>
                        </div>
                        <p className="mt-2 text-sm font-semibold text-[var(--cp-ink)]">{event.title}</p>
                        <p className="mt-1 text-xs text-[var(--cp-muted)]">
                          {event.courseCode} · {event.meta}
                          {event.timeLabel ? ` · ${event.timeLabel}` : ''}
                        </p>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card className="space-y-3">
              <CardTitle>Upcoming</CardTitle>
              {upcoming.length === 0 ? (
                <EmptyState
                  title="Nothing upcoming"
                  message="Add exams or open assignments to populate this timeline."
                />
              ) : (
                <ul className="space-y-3">
                  {upcoming.map((event) => (
                    <li key={event.id} className="border-t border-[var(--cp-border)] pt-3 first:border-t-0 first:pt-0">
                      <button
                        type="button"
                        className="w-full text-left"
                        onClick={() => {
                          setSelectedDate(event.date)
                          setSelectedEvent(event)
                        }}
                      >
                        <p className="text-sm font-semibold text-[var(--cp-ink)]">
                          {event.courseCode} — {event.title}
                        </p>
                        <p className="mt-1 text-xs text-[var(--cp-muted)]">
                          {formatLongDate(event.date)}
                          {event.timeLabel ? ` · ${event.timeLabel}` : ''}
                        </p>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        </div>
      ) : null}

      <Modal
        open={selectedEvent !== null}
        title={selectedEvent?.title ?? 'Event'}
        onClose={() => setSelectedEvent(null)}
        footer={
          <Button variant="secondary" onClick={() => setSelectedEvent(null)}>
            Close
          </Button>
        }
      >
        {selectedEvent ? (
          <div className="space-y-3 text-sm">
            <div className="flex flex-wrap gap-2">
              <Badge tone={selectedEvent.kind === 'exam' ? 'brand' : 'accent'}>
                {selectedEvent.kind === 'exam' ? 'Exam' : 'Assignment'}
              </Badge>
              <Badge tone={urgencyTone(selectedEvent.urgency)}>{selectedEvent.urgency}</Badge>
            </div>
            <p className="text-[var(--cp-muted)]">
              {selectedEvent.courseCode} · {selectedEvent.courseTitle}
            </p>
            <p className="text-[var(--cp-ink)]">{formatLongDate(selectedEvent.date)}</p>
            {selectedEvent.timeLabel ? <p className="text-[var(--cp-ink)]">{selectedEvent.timeLabel}</p> : null}
            <p className="text-slate-600">{selectedEvent.meta}</p>
          </div>
        ) : null}
      </Modal>
    </section>
  )
}
