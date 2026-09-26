import { useCallback, useEffect, useState } from 'react'
import { Alert } from '../components/ui/Alert.tsx'
import { Button } from '../components/ui/Button.tsx'
import { Card, CardTitle } from '../components/ui/Card.tsx'
import { SelectField, TextField } from '../components/ui/Field.tsx'
import { compareScenarios, createScenario, deleteScenario, deleteTarget, getAcademicCourses, getScenarios, getTargets, previewScenario, saveTarget, updateScenario } from '../services/api.ts'
import type { AcademicTarget, SavedScenario, ScenarioAssessment, ScenarioProjection, TargetType } from '../services/api.ts'
import type { CoursePerformance } from '../types/entities.ts'

const metric = (value: number | null) => value === null ? '—' : value.toFixed(2)

export function GoalsPage() {
  const [courses, setCourses] = useState<CoursePerformance[]>([])
  const [targets, setTargets] = useState<AcademicTarget[]>([])
  const [scenarios, setScenarios] = useState<SavedScenario[]>([])
  const [targetValues, setTargetValues] = useState<Record<TargetType, string>>({ SGPA: '', CGPA: '' })
  const [title, setTitle] = useState('')
  const [assessments, setAssessments] = useState<ScenarioAssessment[]>([{ course_id: 0, assessment_type: 'QUIZ', marks_obtained: 0, maximum_marks: 100 }])
  const [projection, setProjection] = useState<ScenarioProjection | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [selectedScenarioIds, setSelectedScenarioIds] = useState<number[]>([])
  const [comparison, setComparison] = useState<SavedScenario[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const refresh = useCallback(async () => {
    const [academicCourses, savedTargets, savedScenarios] = await Promise.all([getAcademicCourses(), getTargets(), getScenarios()])
    setCourses(academicCourses); setTargets(savedTargets); setScenarios(savedScenarios)
    setTargetValues({ SGPA: String(savedTargets.find((t) => t.target_type === 'SGPA')?.target_value ?? ''), CGPA: String(savedTargets.find((t) => t.target_type === 'CGPA')?.target_value ?? '') })
  }, [])
  useEffect(() => { void refresh().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : 'Could not load goals.')) }, [refresh])
  const run = async (action: () => Promise<void>) => {
    setBusy(true); setError(null); setMessage(null)
    try { await action() } catch (cause) { setError(cause instanceof Error ? cause.message : 'The request failed.') } finally { setBusy(false) }
  }
  const updateAssessment = (index: number, patch: Partial<ScenarioAssessment>) => setAssessments((current) => current.map((item, i) => i === index ? { ...item, ...patch } : item))
  const courseFor = (id: number) => courses.find((item) => item.course.id === id)
  return <div className="space-y-6">
    <header><p className="cp-eyebrow">Academic planning</p><h1 className="cp-page-title">Goals &amp; scenarios</h1><p className="mt-2 max-w-2xl text-sm text-[var(--cp-muted)]">Set GPA targets and model assessment marks using your configured course weights. Scenario marks are hypothetical and never overwrite actual marks.</p></header>
    {error ? <Alert tone="error">{error}</Alert> : null}{message ? <Alert tone="success">{message}</Alert> : null}
    <Card><CardTitle>SGPA and CGPA targets</CardTitle><p className="mt-1 text-sm text-[var(--cp-muted)]">Targets update as your academic record changes. GPA uses the 0–10 scale.</p>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">{(['SGPA', 'CGPA'] as const).map((type) => { const target = targets.find((item) => item.target_type === type); return <div key={type} className="rounded-xl border border-[var(--cp-border)] p-4"><div className="flex items-center justify-between"><h3 className="font-semibold">{type} goal</h3><span className="text-sm text-[var(--cp-muted)]">Current {metric(target?.current_value ?? null)}</span></div><div className="mt-3 flex gap-2"><TextField label={type + ' target'} type="number" min="0" max="10" step="0.01" value={targetValues[type]} onChange={(event) => setTargetValues((value) => ({ ...value, [type]: event.target.value }))} /><Button className="mt-6 shrink-0" disabled={busy || !targetValues[type] || Number(targetValues[type]) > 10} onClick={() => void run(async () => { await saveTarget(type, Number(targetValues[type])); await refresh(); setMessage(type + ' target saved.') })}>Save</Button></div>{target ? <p className="mt-2 text-xs text-[var(--cp-muted)]">Target {target.target_value.toFixed(2)} · {target.status === 'INSUFFICIENT_DATA' ? 'Not enough recorded grades yet' : target.status === 'REACHED' ? 'Target reached' : target.remaining?.toFixed(2) + ' points to go'} <button className="ml-2 underline" disabled={busy} onClick={() => void run(async () => { await deleteTarget(type); await refresh(); setMessage(type + ' target removed.') })}>Remove</button></p> : null}</div> })}</div>
    </Card>
    <Card><CardTitle>Build a what-if scenario</CardTitle><p className="mt-1 text-sm text-[var(--cp-muted)]">Enter assessment marks for current-semester courses; the app applies each course’s saved weights and grade bands.</p>
      <div className="mt-4 grid gap-4 sm:grid-cols-2"><TextField label="Scenario name" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Strong finals" /></div>
      <div className="mt-4 space-y-3">{assessments.map((item, index) => <div key={index} className="grid gap-3 rounded-xl border border-[var(--cp-border)] p-3 sm:grid-cols-4">
        <SelectField label="Course" value={item.course_id || ''} onChange={(event) => updateAssessment(index, { course_id: Number(event.target.value) })}><option value="">Select course</option>{courses.map(({ course }) => <option key={course.id} value={course.id}>{course.code} · {course.title}</option>)}</SelectField>
        <TextField label="Assessment type" value={item.assessment_type} onChange={(event) => updateAssessment(index, { assessment_type: event.target.value.toUpperCase() })} placeholder="FINAL" />
        <TextField label="Marks earned" type="number" min="0" step="0.1" value={item.marks_obtained} onChange={(event) => updateAssessment(index, { marks_obtained: Number(event.target.value) })} />
        <div className="flex items-end gap-2"><TextField label="Out of" type="number" min="0.1" step="0.1" value={item.maximum_marks} onChange={(event) => updateAssessment(index, { maximum_marks: Number(event.target.value) })} />{assessments.length > 1 ? <Button variant="ghost" onClick={() => setAssessments((current) => current.filter((_, i) => i !== index))} aria-label="Remove assessment">×</Button> : null}</div>
        {courseFor(item.course_id) ? <p className="sm:col-span-4 text-xs text-[var(--cp-muted)]">Current {courseFor(item.course_id)?.final_score?.toFixed(1) ?? 'incomplete'}% · {courseFor(item.course_id)?.assessments.map((a) => a.assessment_type + ': ' + a.weight_percent + '%').join(' / ')}</p> : null}
      </div>)}</div>
      <div className="mt-4 flex flex-wrap gap-2"><Button variant="secondary" disabled={busy || courses.length === 0} onClick={() => setAssessments((current) => [...current, { course_id: courses[0]?.course.id ?? 0, assessment_type: 'QUIZ', marks_obtained: 0, maximum_marks: 100 }])}>Add assessment</Button><Button disabled={busy || assessments.some((item) => !item.course_id || item.marks_obtained < 0 || item.maximum_marks <= 0 || item.marks_obtained > item.maximum_marks)} onClick={() => void run(async () => { const result = await previewScenario(assessments); setProjection(result); setMessage('Scenario preview updated.') })}>Preview</Button><Button variant="secondary" disabled={busy || !title.trim() || !projection} onClick={() => void run(async () => { if (editingId) await updateScenario(editingId, { title: title.trim(), assessments }); else await createScenario({ title: title.trim(), assessments }); await refresh(); setMessage(editingId ? 'Scenario updated.' : 'Scenario saved.'); setTitle(''); setEditingId(null) })}>{editingId ? 'Update scenario' : 'Save scenario'}</Button>{editingId ? <Button variant="ghost" onClick={() => { setEditingId(null); setTitle(''); setProjection(null) }}>Cancel edit</Button> : null}</div>
      {projection ? <div className="mt-5 grid gap-3 rounded-xl bg-[var(--cp-brand-wash)] p-4 sm:grid-cols-4"><Metric label="Current SGPA" value={projection.current_sgpa.value} /><Metric label="Projected SGPA" value={projection.projected_sgpa.value} /><Metric label="Current CGPA" value={projection.current_cgpa.value} /><Metric label="Projected CGPA" value={projection.projected_cgpa.value} /></div> : null}
    </Card>
    <Card><CardTitle>Saved scenarios</CardTitle>{scenarios.length === 0 ? <p className="mt-3 text-sm text-[var(--cp-muted)]">No saved scenarios yet. Preview one above, then save it for later comparison.</p> : <><div className="mt-4 grid gap-3 md:grid-cols-2">{scenarios.map((scenario) => <article key={scenario.id} className="rounded-xl border border-[var(--cp-border)] p-4"><div className="flex items-start justify-between gap-3"><label className="flex gap-2"><input type="checkbox" checked={selectedScenarioIds.includes(scenario.id)} onChange={(event) => setSelectedScenarioIds((ids) => event.target.checked ? [...ids, scenario.id].slice(-5) : ids.filter((id) => id !== scenario.id))} aria-label={'Select ' + scenario.title + ' to compare'} /><span><h3 className="font-semibold">{scenario.title}</h3><p className="mt-1 text-xs text-[var(--cp-muted)]">{scenario.assessments.length} assessment changes · {scenario.assessments.map((a) => a.assessment_type + ' ' + a.marks_obtained + '/' + a.maximum_marks).join(' · ')}</p></span></label><Button variant="ghost" disabled={busy} onClick={() => void run(async () => { await deleteScenario(scenario.id); setSelectedScenarioIds((ids) => ids.filter((id) => id !== scenario.id)); await refresh(); setMessage('Scenario deleted.') })}>Delete</Button></div><div className="mt-3 flex gap-5 text-sm"><span>SGPA <b>{metric(scenario.projection.projected_sgpa.value)}</b></span><span>CGPA <b>{metric(scenario.projection.projected_cgpa.value)}</b></span></div><Button className="mt-3" variant="secondary" size="sm" onClick={() => { setEditingId(scenario.id); setTitle(scenario.title); setAssessments(scenario.assessments); setProjection(scenario.projection); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>Edit scenario</Button></article>)}</div><div className="mt-4"><Button variant="secondary" disabled={busy || selectedScenarioIds.length < 2} onClick={() => void run(async () => { const result = await compareScenarios(selectedScenarioIds); setComparison(result.scenarios) })}>Compare selected ({selectedScenarioIds.length})</Button></div>{comparison.length > 0 ? <div className="mt-4 grid gap-3 sm:grid-cols-2">{comparison.map((scenario) => <div key={scenario.id} className="rounded-lg bg-[var(--cp-brand-wash)] p-4"><p className="font-semibold">{scenario.title}</p><p className="mt-2 text-sm">Projected SGPA <b>{metric(scenario.projection.projected_sgpa.value)}</b> ({scenario.projection.projected_sgpa.value !== null && scenario.projection.current_sgpa.value !== null ? (scenario.projection.projected_sgpa.value - scenario.projection.current_sgpa.value >= 0 ? '+' : '') + (scenario.projection.projected_sgpa.value - scenario.projection.current_sgpa.value).toFixed(2) : '—'})</p><p className="text-sm">Projected CGPA <b>{metric(scenario.projection.projected_cgpa.value)}</b></p></div>)}</div> : null}</>}</Card>
  </div>
}
function Metric({ label, value }: { label: string; value: number | null }) { return <div><p className="text-xs text-[var(--cp-muted)]">{label}</p><p className="mt-1 text-xl font-bold">{metric(value)}</p></div> }
