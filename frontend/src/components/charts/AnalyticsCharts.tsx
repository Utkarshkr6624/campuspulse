import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { CHART_COLORS, GRADE_CHART_PALETTE } from '../../constants/chartTheme.ts'

type TooltipPayload = {
  name?: string
  value?: number | string
  payload?: Record<string, unknown>
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: TooltipPayload[]
  label?: string
}) {
  if (!active || !payload?.length) {
    return null
  }
  return (
    <div className="rounded-lg border border-[var(--cp-border)] bg-white px-3 py-2 text-xs shadow-[var(--cp-shadow)]">
      {label ? <p className="mb-1 font-semibold text-[var(--cp-ink)]">{label}</p> : null}
      {payload.map((item) => (
        <p key={`${item.name}-${item.value}`} className="text-[var(--cp-muted)]">
          {item.name}: <span className="font-semibold text-[var(--cp-ink)]">{item.value}</span>
        </p>
      ))}
    </div>
  )
}

export function PerformanceLineChart({
  data,
}: {
  data: Array<{ label: string; percentage: number; course: string }>
}) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
          <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fill: CHART_COLORS.muted, fontSize: 11 }} />
          <YAxis domain={[0, 100]} tick={{ fill: CHART_COLORS.muted, fontSize: 11 }} unit="%" />
          <Tooltip content={<ChartTooltip />} />
          <Line
            type="monotone"
            dataKey="percentage"
            name="Score"
            stroke={CHART_COLORS.brand}
            strokeWidth={2.5}
            dot={{ r: 4, fill: CHART_COLORS.accent }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function GpaHistoryLineChart({
  data,
}: {
  data: Array<{ semester: string; gpa: number }>
}) {
  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
          <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" />
          <XAxis dataKey="semester" tick={{ fill: CHART_COLORS.muted, fontSize: 11 }} />
          <YAxis domain={[0, 'auto']} tick={{ fill: CHART_COLORS.muted, fontSize: 11 }} />
          <Tooltip content={<ChartTooltip />} />
          <Line
            type="monotone"
            dataKey="gpa"
            name="SGPA"
            stroke={CHART_COLORS.brand}
            strokeWidth={2.5}
            dot={{ r: 4, fill: CHART_COLORS.accent }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function CourseScoreBarChart({
  data,
}: {
  data: Array<{ name: string; score: number }>
}) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
          <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fill: CHART_COLORS.muted, fontSize: 11 }} />
          <YAxis domain={[0, 100]} tick={{ fill: CHART_COLORS.muted, fontSize: 11 }} unit="%" />
          <Tooltip content={<ChartTooltip />} />
          <Bar dataKey="score" name="Score" fill={CHART_COLORS.brand} radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function AttendanceBarChart({
  data,
}: {
  data: Array<{ name: string; percentage: number }>
}) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
          <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fill: CHART_COLORS.muted, fontSize: 11 }} />
          <YAxis domain={[0, 100]} tick={{ fill: CHART_COLORS.muted, fontSize: 11 }} unit="%" />
          <Tooltip content={<ChartTooltip />} />
          <Bar dataKey="percentage" name="Attendance" fill={CHART_COLORS.success} radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function GradeDonutChart({
  data,
}: {
  data: Array<{ letter: string; count: number }>
}) {
  const filtered = data.filter((item) => item.count > 0)
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={filtered}
            dataKey="count"
            nameKey="letter"
            innerRadius={55}
            outerRadius={90}
            paddingAngle={2}
          >
            {filtered.map((entry, index) => (
              <Cell
                key={entry.letter}
                fill={GRADE_CHART_PALETTE[index % GRADE_CHART_PALETTE.length]}
              />
            ))}
          </Pie>
          <Tooltip content={<ChartTooltip />} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
