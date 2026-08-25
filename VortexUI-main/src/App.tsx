import { useEffect, useState, useRef } from 'react'

/* ── Design tokens (Strict Figma Make High-Tech Dark Mode) ────────── */
const GOLD = '#ff0000' // primary accent (electric crimson / neon red)
const DEEP = '#af0404' // deep red / secondary
const SURFACE = '#414141'
const CANVAS = '#252525'
const HAIRLINE = '#565656'
const PLATINUM = '#eeeeee'
const MUTED = '#9a9a9a'
const SUCCESS = '#ff0000'
const IDLE = '#6b6b6b'

const cardShadow = '0 10px 30px rgba(0,0,0,0.35)'
const goldGlow = '0 0 20px rgba(255,0,0,0.18)'

type NavKey = 'command' | 'approvals' | 'analytics' | 'settings'

/* ── Icons (simple stroke set) ───────────────────────────────────── */
type IconName =
  | 'infinity'
  | 'command'
  | 'check'
  | 'chart'
  | 'settings'
  | 'search'
  | 'target'
  | 'pen'
  | 'palette'
  | 'send'
  | 'activity'
  | 'play'
  | 'refresh'
  | 'close'
  | 'pause'

const PATHS: Record<IconName, React.ReactNode> = {
  infinity: (
    <path d="M6 12c0-2 1.6-3.5 3-3.5S11.5 10 12 12s1.6 3.5 3 3.5S18 14 18 12s-1.6-3.5-3-3.5-2.5 1.5-3 3.5-1.6 3.5-3 3.5S6 14 6 12Z" />
  ),
  command: <path d="M9 6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6Z" />,
  check: <path d="m5 12 5 5L19 7" />,
  chart: <path d="M4 20V10M10 20V4M16 20v-6M22 20H2" />,
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </>
  ),
  target: (
    <>
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="3.5" />
    </>
  ),
  pen: <path d="M4 20h4L19 9a2 2 0 0 0-3-3L5 17v3ZM14 6l4 4" />,
  palette: (
    <>
      <path d="M12 3a9 9 0 0 0 0 18c1.5 0 2-1 2-2 0-1.5 1-2 2-2h1a4 4 0 0 0 4-4 9 9 0 0 0-9-8Z" />
      <circle cx="7.5" cy="12" r="1" />
      <circle cx="10" cy="7.5" r="1" />
      <circle cx="15" cy="7.5" r="1" />
    </>
  ),
  send: <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z" />,
  activity: <path d="M3 12h4l3 8 4-16 3 8h4" />,
  play: <path d="M6 4l14 8-14 8V4Z" />,
  refresh: <path d="M21 12a9 9 0 1 1-3-6.7M21 4v5h-5" />,
  close: <path d="M6 6l12 12M18 6 6 18" />,
  pause: <path d="M8 5v14M16 5v14" />,
}

function Icon({
  name,
  size = 18,
  color = 'currentColor',
  strokeWidth = 1.75,
  fill = false,
}: {
  name: IconName
  size?: number
  color?: string
  strokeWidth?: number
  fill?: boolean
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={fill ? color : 'none'}
      stroke={fill ? 'none' : color}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {PATHS[name]}
    </svg>
  )
}

/* ── Small primitives ────────────────────────────────────────────── */
function Card({
  children,
  className = '',
  active = false,
  onClick,
  style,
}: {
  children: React.ReactNode
  className?: string
  active?: boolean
  onClick?: () => void
  style?: React.CSSProperties
}) {
  return (
    <div
      onClick={onClick}
      className={`rounded-2xl border transition-all duration-300 ${className} ${onClick ? 'cursor-pointer hover:-translate-y-0.5' : ''}`}
      style={{
        backgroundColor: SURFACE,
        borderColor: active ? GOLD : HAIRLINE,
        backdropFilter: 'blur(12px)',
        boxShadow: active ? `${cardShadow}, ${goldGlow}` : cardShadow,
        ...style,
      }}
    >
      {children}
    </div>
  )
}

function StatusPill({
  kind,
  label,
}: {
  kind: 'awaiting' | 'queued' | 'success' | 'idle'
  label: string
}) {
  const map = {
    awaiting: { dot: GOLD, text: GOLD, bg: 'rgba(255,0,0,0.12)', glow: true },
    queued: { dot: IDLE, text: MUTED, bg: 'rgba(107,114,128,0.14)', glow: false },
    success: { dot: SUCCESS, text: SUCCESS, bg: 'rgba(255,0,0,0.12)', glow: false },
    idle: { dot: IDLE, text: MUTED, bg: 'rgba(107,114,128,0.14)', glow: false },
  }[kind] || { dot: IDLE, text: MUTED, bg: 'rgba(107,114,128,0.14)', glow: false }

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-mono text-[11px] font-medium"
      style={{ backgroundColor: map.bg, color: map.text, letterSpacing: '0.02em' }}
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{
          backgroundColor: map.dot,
          animation: map.glow ? 'gold-breathe 2s ease-in-out infinite' : undefined,
        }}
      />
      {label}
    </span>
  )
}

/* ── Sidebar ─────────────────────────────────────────────────────── */
function Sidebar({
  active,
  onNav,
  hasPendingApproval,
  isConnected,
}: {
  active: NavKey
  onNav: (k: NavKey) => void
  hasPendingApproval: boolean
  isConnected: boolean
}) {
  const items: { key: NavKey; icon: IconName; label: string; badge?: string }[] = [
    { key: 'command', icon: 'command', label: 'Command Center' },
    { key: 'approvals', icon: 'check', label: 'Approvals', badge: hasPendingApproval ? '1' : undefined },
    { key: 'analytics', icon: 'chart', label: 'Analytics' },
    { key: 'settings', icon: 'settings', label: 'Settings' },
  ]

  return (
    <aside
      className="flex w-[260px] shrink-0 flex-col border-r px-4 py-6"
      style={{ backgroundColor: '#000000', borderColor: HAIRLINE }}
    >
      {/* Brand */}
      <div className="flex items-center gap-3 px-2">
        <div
          className="flex h-10 w-10 items-center justify-center rounded-xl"
          style={{
            background: 'linear-gradient(135deg, #ff4d4d, #ff0000)',
            color: CANVAS,
            boxShadow: goldGlow,
          }}
        >
          <Icon name="infinity" size={22} strokeWidth={2} color={CANVAS} />
        </div>
        <div className="leading-tight">
          <div className="text-[16px] font-bold" style={{ color: PLATINUM }}>
            Noir
          </div>
          <div className="font-mono text-[10px] tracking-[0.18em]" style={{ color: MUTED }}>
            CONTENT ENGINE
          </div>
        </div>
      </div>

      <nav className="mt-8 flex flex-col gap-1">
        {items.map((it) => {
          const isActive = active === it.key
          return (
            <button
              key={it.key}
              onClick={() => onNav(it.key)}
              className="relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[14px] transition-colors"
              style={{
                color: isActive ? GOLD : MUTED,
                backgroundColor: isActive ? 'rgba(255,0,0,0.10)' : 'transparent',
                fontWeight: isActive ? 600 : 500,
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.color = PLATINUM
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.color = MUTED
              }}
            >
              {isActive && (
                <span
                  className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-full"
                  style={{ backgroundColor: GOLD, boxShadow: goldGlow }}
                />
              )}
              <span className="flex w-5 justify-center">
                <Icon name={it.icon} size={17} />
              </span>
              <span className="flex-1">{it.label}</span>
              {it.badge && (
                <span
                  className="flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 font-mono text-[11px] font-bold animate-pulse"
                  style={{ backgroundColor: GOLD, color: CANVAS }}
                >
                  {it.badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      <div className="mt-auto">
        <div
          className="flex items-center gap-3 rounded-xl border px-3 py-3"
          style={{ borderColor: HAIRLINE, backgroundColor: 'rgba(57,62,70,0.5)' }}
        >
          <div
            className="flex h-9 w-9 items-center justify-center rounded-full text-[13px] font-bold"
            style={{ backgroundColor: HAIRLINE, color: PLATINUM }}
          >
            PU
          </div>
          <div className="min-w-0 flex-1 leading-tight">
            <div className="truncate text-[13px] font-semibold" style={{ color: PLATINUM }}>
              Pushkar Ugale
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className="h-2 w-2 rounded-full"
                style={{
                  backgroundColor: isConnected ? SUCCESS : IDLE,
                  animation: isConnected ? 'loop-pulse 2s ease-in-out infinite' : undefined,
                }}
              />
              <span className="text-[11px]" style={{ color: MUTED }}>
                {isConnected ? 'System Live & Connected' : 'Connecting to Engine...'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}

/* ── Stats ───────────────────────────────────────────────────────── */
function StatCard({ s }: { s: { label: string; value: string; sub: string; subColor: string } }) {
  return (
    <Card className="p-4">
      <div className="text-[12px] font-medium" style={{ color: MUTED }}>
        {s.label}
      </div>
      <div className="mt-2 text-[28px] font-bold leading-none" style={{ color: PLATINUM }}>
        {s.value}
      </div>
      <div className="mt-2 font-mono text-[11px]" style={{ color: s.subColor }}>
        {s.sub}
      </div>
    </Card>
  )
}

/* ── Pipeline stepper ────────────────────────────────────────────── */
type NodeState = 'active' | 'queued' | 'completed'

const PIPELINE_DEF: { id: string; icon: IconName; label: string }[] = [
  { id: 'researcher', icon: 'search', label: 'Research' },
  { id: 'hook_writer', icon: 'target', label: 'Hooks' },
  { id: 'script_writer', icon: 'pen', label: 'Scripts' },
  { id: 'designer', icon: 'palette', label: 'Design' },
  { id: 'publisher', icon: 'send', label: 'Publish' },
  { id: 'analyst', icon: 'chart', label: 'Analyze' },
]

function PipelineTrack({ lit, gate }: { lit: boolean; gate: boolean }) {
  return (
    <div className="flex min-w-[48px] flex-1 flex-col items-center gap-1">
      <div
        className="h-[2px] w-full rounded-full"
        style={
          lit
            ? {
                backgroundImage:
                  'repeating-linear-gradient(90deg, rgba(255,0,0,0.9) 0 8px, transparent 8px 16px)',
                backgroundSize: '24px 2px',
                animation: 'flow-dash 0.8s linear infinite',
                boxShadow: '0 0 8px rgba(255,0,0,0.4)',
              }
            : { backgroundColor: HAIRLINE }
        }
      />
      {gate && (
        <span className="flex items-center gap-1 font-mono text-[9px] tracking-wide" style={{ color: MUTED }}>
          <Icon name="pause" size={9} strokeWidth={2} /> gate
        </span>
      )}
    </div>
  )
}

function PipelineNode({
  n,
  idx,
  state,
  onClick,
}: {
  n: (typeof PIPELINE_DEF)[number]
  idx: number
  state: NodeState
  onClick: () => void
}) {
  const isActive = state === 'active' || state === 'awaiting'
  const isDone = state === 'completed'

  return (
    <div className="flex flex-col items-center gap-2 cursor-pointer group" onClick={onClick}>
      <div
        className="flex h-14 w-14 items-center justify-center rounded-2xl border transition-transform group-hover:scale-105"
        style={{
          backgroundColor: SURFACE,
          borderColor: isActive ? GOLD : isDone ? SUCCESS : HAIRLINE,
          boxShadow: isActive ? goldGlow : 'none',
          animation: isActive ? 'gold-breathe 2.4s ease-in-out infinite' : undefined,
        }}
      >
        <Icon name={n.icon} size={22} color={isActive ? GOLD : isDone ? SUCCESS : PLATINUM} />
      </div>
      <div className="text-center leading-tight">
        <div className="font-mono text-[10px]" style={{ color: MUTED }}>
          0{idx + 1}
        </div>
        <div className="text-[12px] font-semibold" style={{ color: isActive ? GOLD : PLATINUM }}>
          {n.label}
        </div>
      </div>
      {isActive ? (
        <StatusPill kind="awaiting" label="AWAITING" />
      ) : isDone ? (
        <StatusPill kind="success" label="DONE" />
      ) : (
        <StatusPill kind="queued" label="QUEUED" />
      )}
    </div>
  )
}

function Pipeline({
  agentStatuses,
  isRunning,
  cycleNumber,
  onNodeClick,
}: {
  agentStatuses: Record<string, string>
  isRunning: boolean
  cycleNumber: number
  onNodeClick: (agentId: string) => void
}) {
  return (
    <Card className="p-5">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-[16px] font-bold" style={{ color: PLATINUM }}>
            Pipeline Flow
          </h2>
          <p className="text-[12px]" style={{ color: MUTED }}>
            6 autonomous agents · human gates between phases
          </p>
        </div>
        <StatusPill
          kind={isRunning ? 'awaiting' : 'idle'}
          label={isRunning ? `RUNNING · CYCLE #${cycleNumber}` : 'IDLE'}
        />
      </div>
      <div className="flex items-start">
        {PIPELINE_DEF.map((n, i) => {
          const rawStatus = agentStatuses[n.id] || (n.id === 'researcher' ? 'awaiting' : 'queued')
          const state: NodeState =
            rawStatus === 'active' || rawStatus === 'awaiting' || rawStatus === 'awaiting_approval'
              ? 'active'
              : rawStatus === 'completed'
                ? 'completed'
                : 'queued'

          return (
            <div key={n.label} className="flex flex-1 items-start" style={{ flex: i === 0 ? '0 0 auto' : 1 }}>
              {i > 0 && <PipelineTrack lit={Boolean(state === 'active')} gate={i <= 4} />}
              <PipelineNode n={n} idx={i} state={state} onClick={() => onNodeClick(n.id)} />
            </div>
          )
        })}
      </div>
    </Card>
  )
}

/* ── Agent roster ────────────────────────────────────────────────── */
const AGENTS = [
  { id: 'researcher', num: '01', name: 'The Researcher', dept: 'Research Dept.' },
  { id: 'hook_writer', num: '02', name: 'The Hook Writer', dept: 'Creative Dept.' },
  { id: 'script_writer', num: '03', name: 'The Script Writer', dept: 'Creative Dept.' },
  { id: 'designer', num: '04', name: 'The Designer', dept: 'Design Dept.' },
  { id: 'publisher', num: '07', name: 'The Publisher', dept: 'Distribution Dept.' },
  { id: 'analyst', num: '05', name: 'The Analyst', dept: 'Insights Dept.' },
]

function AgentCard({
  a,
  status,
  onClick,
}: {
  a: (typeof AGENTS)[number]
  status: string
  onClick: () => void
}) {
  const isActive = status === 'active' || status === 'awaiting' || status === 'awaiting_approval'
  const isDone = status === 'completed'

  return (
    <Card
      onClick={onClick}
      className="p-4 transition-transform hover:-translate-y-0.5"
      active={isActive}
      style={{ borderRadius: 12 }}
    >
      <div className="flex items-start justify-between">
        <span className="font-mono text-[11px] tracking-[0.12em]" style={{ color: MUTED }}>
          AGENT {a.num}
        </span>
        <span
          className="h-2 w-2 rounded-full"
          style={{
            backgroundColor: isActive ? GOLD : isDone ? SUCCESS : IDLE,
            animation: isActive ? 'gold-breathe 2s ease-in-out infinite' : undefined,
          }}
        />
      </div>
      <div className="mt-3 text-[15px] font-bold" style={{ color: PLATINUM }}>
        {a.name}
      </div>
      <div className="text-[12px]" style={{ color: MUTED }}>
        {a.dept}
      </div>
      <div className="mt-3">
        <StatusPill
          kind={isActive ? 'awaiting' : isDone ? 'success' : 'queued'}
          label={isActive ? 'AWAITING APPROVAL' : isDone ? 'COMPLETED' : 'QUEUED'}
        />
      </div>
    </Card>
  )
}

/* ── Activity terminal ───────────────────────────────────────────── */
function Terminal({ logs }: { logs: { t: string; dot: string; text: string }[] }) {
  return (
    <Card className="overflow-hidden p-0" style={{ borderRadius: 12 }}>
      <div className="flex items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Icon name="activity" size={14} color={GOLD} />
          <span className="font-mono text-[11px]" style={{ color: MUTED }}>
            live_activity.log
          </span>
        </div>
        <span className="flex items-center gap-1.5 font-mono text-[10px]" style={{ color: SUCCESS }}>
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: SUCCESS, animation: 'loop-pulse 2s ease-in-out infinite' }}
          />
          STREAMING
        </span>
      </div>
      <ul
        className="max-h-[220px] divide-y overflow-y-auto font-mono text-[11.5px]"
        style={{ backgroundColor: CANVAS, borderColor: HAIRLINE }}
      >
        {logs.map((l, i) => (
          <li
            key={`${l.t}-${i}`}
            className="flex items-center gap-2.5 px-4 py-2"
            style={{ borderColor: 'rgba(86,86,86,0.35)' }}
          >
            <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ backgroundColor: l.dot }} />
            <span className="shrink-0 tabular-nums" style={{ color: MUTED }}>
              {l.t}
            </span>
            <span className="truncate" style={{ color: PLATINUM }}>
              {l.text}
            </span>
          </li>
        ))}
      </ul>
    </Card>
  )
}

/* ── Score Bar ───────────────────────────────────────────────────── */
function ScoreBar({ v }: { v: number }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full" style={{ backgroundColor: CANVAS }}>
      <div
        className="h-full rounded-full"
        style={{
          width: `${v}%`,
          background: 'linear-gradient(90deg, #af0404, #ff0000)',
          boxShadow: '0 0 10px rgba(255,0,0,0.5)',
        }}
      />
    </div>
  )
}

/* ── Approval modal ──────────────────────────────────────────────── */
const DEFAULT_HOOKS = [
  { rank: 1, text: 'The AI trend nobody is talking about (yet)', score: 94, tag: 'Explainer' },
  { rank: 2, text: 'I let 6 agents run my content for a week', score: 88, tag: 'Story' },
  { rank: 3, text: 'Why your feed feels the same everywhere', score: 81, tag: 'Contrarian' },
  { rank: 4, text: 'Stop scripting. Start looping.', score: 73, tag: 'Punchy' },
]

function ApprovalModal({
  onClose,
  reviewData,
  onAction,
}: {
  onClose: () => void
  reviewData: any
  onAction: (action: string, feedback: string) => void
}) {
  const [feedback, setFeedback] = useState('')

  const trends =
    reviewData?.content?.trends?.map((t: any, i: number) => ({
      rank: i + 1,
      text: t.title || t.description,
      score: t.virality_score ? Math.round(t.virality_score * 10) : 85,
      tag: t.platform || 'General',
    })) || DEFAULT_HOOKS

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-6"
      style={{ backgroundColor: 'rgba(20,24,30,0.72)', backdropFilter: 'blur(6px)' }}
      onClick={onClose}
    >
      <div
        className="flex max-h-[86vh] w-full max-w-[720px] flex-col overflow-hidden rounded-2xl border"
        style={{ backgroundColor: SURFACE, borderColor: HAIRLINE, boxShadow: `${cardShadow}, ${goldGlow}` }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-5" style={{ borderColor: HAIRLINE }}>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-[22px] font-bold" style={{ color: PLATINUM }}>
                {reviewData?.title || 'Gate 01: Research & Trend Review'}
              </h2>
              <span
                className="rounded-lg px-2 py-0.5 font-mono text-[11px] font-semibold"
                style={{ backgroundColor: 'rgba(255,0,0,0.12)', color: GOLD }}
              >
                Cycle #1
              </span>
            </div>
            <p className="mt-1 text-[13px]" style={{ color: MUTED }}>
              Human-in-the-loop checkpoint · steer the Hook Writer before it runs
            </p>
          </div>
          <button
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-lg hover:opacity-80"
            style={{ color: MUTED, backgroundColor: CANVAS }}
          >
            <Icon name="close" size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 space-y-3 overflow-y-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[11px] tracking-[0.12em]" style={{ color: MUTED }}>
              TOP TRENDING HOOKS · EST. VIRAL SCORE
            </span>
            <span className="font-mono text-[11px]" style={{ color: SUCCESS }}>
              {trends.length} trends scored
            </span>
          </div>
          {trends.map((h: any) => (
            <div
              key={h.rank}
              className="rounded-xl border p-4"
              style={{ backgroundColor: CANVAS, borderColor: HAIRLINE }}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <span
                    className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md font-mono text-[12px] font-bold"
                    style={{
                      backgroundColor: h.rank === 1 ? GOLD : HAIRLINE,
                      color: h.rank === 1 ? CANVAS : PLATINUM,
                    }}
                  >
                    {h.rank}
                  </span>
                  <div>
                    <div className="text-[14px] font-semibold" style={{ color: PLATINUM }}>
                      {h.text}
                    </div>
                    <span className="font-mono text-[11px]" style={{ color: MUTED }}>
                      {h.tag}
                    </span>
                  </div>
                </div>
                <span className="font-mono text-[16px] font-bold" style={{ color: GOLD }}>
                  {h.score}
                </span>
              </div>
              <div className="mt-3">
                <ScoreBar v={h.score} />
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="space-y-3 border-t px-6 py-5" style={{ borderColor: HAIRLINE }}>
          <input
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Add steering feedback for Hook Writer..."
            className="w-full rounded-xl border px-4 py-3 text-[14px] outline-none"
            style={{ backgroundColor: CANVAS, borderColor: HAIRLINE, color: PLATINUM }}
            onFocus={(e) => (e.currentTarget.style.borderColor = GOLD)}
            onBlur={(e) => (e.currentTarget.style.borderColor = HAIRLINE)}
          />
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => onAction('approve', feedback)}
              className="flex items-center gap-2 rounded-lg px-5 py-2.5 text-[14px] font-bold transition-transform hover:scale-105"
              style={{ backgroundColor: GOLD, color: PLATINUM, boxShadow: goldGlow }}
            >
              <Icon name="check" size={16} strokeWidth={2.25} color={PLATINUM} /> Approve &amp; Proceed
            </button>
            <button
              onClick={() => onAction('revision_requested', feedback)}
              className="flex items-center gap-2 rounded-lg border px-5 py-2.5 text-[14px] font-semibold transition-transform hover:scale-105"
              style={{ borderColor: GOLD, color: GOLD, backgroundColor: 'transparent' }}
            >
              <Icon name="refresh" size={15} /> Request Revision
            </button>
            <button
              onClick={() => onAction('reject', feedback)}
              className="ml-auto flex items-center gap-2 rounded-lg px-4 py-2.5 text-[14px] font-semibold hover:opacity-80"
              style={{ color: DEEP, backgroundColor: 'transparent' }}
            >
              <Icon name="close" size={15} strokeWidth={2} /> Reject Trend
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Command Center view ─────────────────────────────────────────── */
function CommandCenter({
  stats,
  agentStatuses,
  isRunning,
  cycleNumber,
  logs,
  onStart,
  onInspectNode,
}: {
  stats: { trends: number; ideas: number; hooks: number; published: number }
  agentStatuses: Record<string, string>
  isRunning: boolean
  cycleNumber: number
  logs: any[]
  onStart: () => void
  onInspectNode: (nodeId: string) => void
}) {
  const statList = [
    { label: 'Trends Discovered', value: String(stats.trends || 24), sub: '+12% this cycle', subColor: SUCCESS },
    { label: 'Content Ideas', value: String(stats.ideas || 18), sub: '8 high urgency', subColor: GOLD },
    { label: 'Hooks Generated', value: String(stats.hooks || 80), sub: '10 winning hooks', subColor: GOLD },
    { label: 'Published Posts', value: String(stats.published || 42), sub: '6 networks live', subColor: MUTED },
  ]

  return (
    <div className="mx-auto max-w-[1180px] px-8 py-7">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-bold leading-tight" style={{ color: PLATINUM }}>
            Command Center
          </h1>
          <p className="text-[13px]" style={{ color: MUTED }}>
            Autonomous multi-agent content engine · orchestrating cycle #{cycleNumber}
          </p>
        </div>
        <button
          onClick={onStart}
          disabled={isRunning}
          className="flex items-center gap-2 rounded-full px-5 py-2.5 text-[14px] font-bold transition-transform hover:scale-[1.02] disabled:opacity-50"
          style={{
            background: 'linear-gradient(135deg, #ff4d4d, #ff0000)',
            color: PLATINUM,
            boxShadow: `0 6px 20px rgba(255,0,0,0.35)`,
          }}
        >
          <Icon name="play" size={15} fill color={PLATINUM} /> {isRunning ? 'Running...' : 'Start Pipeline'}
        </button>
      </header>

      <section className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {statList.map((s) => (
          <StatCard key={s.label} s={s} />
        ))}
      </section>

      <section className="mt-6">
        <Pipeline
          agentStatuses={agentStatuses}
          isRunning={isRunning}
          cycleNumber={cycleNumber}
          onNodeClick={onInspectNode}
        />
      </section>

      <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h2 className="mb-3 text-[16px] font-bold" style={{ color: PLATINUM }}>
            Agent Roster
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {AGENTS.map((a) => (
              <AgentCard
                key={a.num}
                a={a}
                status={agentStatuses[a.id] || (a.id === 'researcher' ? 'awaiting' : 'queued')}
                onClick={() => onInspectNode(a.id)}
              />
            ))}
          </div>
        </div>
        <div className="lg:col-span-1">
          <h2 className="mb-3 text-[16px] font-bold" style={{ color: PLATINUM }}>
            Live Activity
          </h2>
          <Terminal logs={logs} />
        </div>
      </section>
    </div>
  )
}

/* ── Analytics view ──────────────────────────────────────────────── */
function ViewHeader({ title, sub }: { title: string; sub: string }) {
  return (
    <div>
      <h1 className="text-[28px] font-bold leading-tight" style={{ color: PLATINUM }}>
        {title}
      </h1>
      <p className="text-[13px]" style={{ color: MUTED }}>
        {sub}
      </p>
    </div>
  )
}

const ANALYTICS_KPIS = [
  { label: 'Avg. Viral Score', value: '84', sub: '+6 vs last cycle' },
  { label: 'Reach', value: '1.2M', sub: 'across 6 networks' },
  { label: 'Approval Rate', value: '92%', sub: '11 of 12 gates' },
  { label: 'Cycle Time', value: '4h 12m', sub: '−38m faster' },
]

const NETWORK_PERF = [
  { name: 'X / Twitter', v: 92 },
  { name: 'LinkedIn', v: 78 },
  { name: 'Instagram', v: 64 },
  { name: 'TikTok', v: 88 },
  { name: 'YouTube', v: 51 },
  { name: 'Threads', v: 43 },
]

const WEEKLY = [38, 52, 44, 66, 59, 81, 72]

function AnalyticsView() {
  return (
    <div className="mx-auto max-w-[1180px] px-8 py-7">
      <ViewHeader title="Analytics" sub="Performance across the last 12 pipeline cycles" />

      <section className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {ANALYTICS_KPIS.map((k) => (
          <Card key={k.label} className="p-4">
            <div className="text-[12px] font-medium" style={{ color: MUTED }}>
              {k.label}
            </div>
            <div className="mt-2 text-[28px] font-bold leading-none" style={{ color: PLATINUM }}>
              {k.value}
            </div>
            <div className="mt-2 font-mono text-[11px]" style={{ color: GOLD }}>
              {k.sub}
            </div>
          </Card>
        ))}
      </section>

      <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Weekly output bar chart */}
        <Card className="p-5">
          <h2 className="text-[16px] font-bold" style={{ color: PLATINUM }}>
            Weekly Output
          </h2>
          <p className="text-[12px]" style={{ color: MUTED }}>
            Posts published per day
          </p>
          <div className="mt-6 flex h-40 items-end gap-3">
            {WEEKLY.map((v, i) => (
              <div key={i} className="flex h-full flex-1 flex-col items-center justify-end gap-2">
                <div
                  className="w-full rounded-t-md"
                  style={{
                    height: `${v}%`,
                    background: 'linear-gradient(180deg, #ff0000, #af0404)',
                    boxShadow: '0 0 12px rgba(255,0,0,0.25)',
                  }}
                />
                <span className="font-mono text-[10px]" style={{ color: MUTED }}>
                  {['M', 'T', 'W', 'T', 'F', 'S', 'S'][i]}
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Network performance */}
        <Card className="p-5">
          <h2 className="text-[16px] font-bold" style={{ color: PLATINUM }}>
            Network Performance
          </h2>
          <p className="text-[12px]" style={{ color: MUTED }}>
            Engagement index by channel
          </p>
          <div className="mt-5 space-y-3.5">
            {NETWORK_PERF.map((n) => (
              <div key={n.name}>
                <div className="mb-1 flex items-center justify-between text-[12px]">
                  <span style={{ color: PLATINUM }}>{n.name}</span>
                  <span className="font-mono" style={{ color: MUTED }}>
                    {n.v}
                  </span>
                </div>
                <ScoreBar v={n.v} />
              </div>
            ))}
          </div>
        </Card>
      </section>
    </div>
  )
}

/* ── Settings view ───────────────────────────────────────────────── */
function Toggle({ on, onToggle }: { on: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      className="relative h-6 w-11 rounded-full transition-colors"
      style={{ backgroundColor: on ? GOLD : HAIRLINE }}
    >
      <span
        className="absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all"
        style={{ left: on ? '22px' : '2px' }}
      />
    </button>
  )
}

function SettingsRow({
  title,
  desc,
  children,
}: {
  title: string
  desc: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-4">
      <div>
        <div className="text-[14px] font-semibold" style={{ color: PLATINUM }}>
          {title}
        </div>
        <div className="text-[12px]" style={{ color: MUTED }}>
          {desc}
        </div>
      </div>
      {children}
    </div>
  )
}

function SettingsView() {
  const [autopilot, setAutopilot] = useState(true)
  const [notify, setNotify] = useState(true)
  const [darkGates, setDarkGates] = useState(false)
  const [autonomy, setAutonomy] = useState('Balanced')
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="mx-auto max-w-[820px] px-8 py-7">
      <ViewHeader title="Settings" sub="Configure how the engine runs and asks for approval" />

      {/* Engine */}
      <Card className="mt-6 px-5 py-1">
        <div className="border-b py-3" style={{ borderColor: HAIRLINE }}>
          <span className="font-mono text-[11px] tracking-[0.12em]" style={{ color: GOLD }}>
            ENGINE
          </span>
        </div>
        <div className="divide-y" style={{ borderColor: 'rgba(86,86,86,0.4)' }}>
          <SettingsRow title="Autopilot" desc="Run cycles continuously without manual start">
            <Toggle on={autopilot} onToggle={() => setAutopilot((v) => !v)} />
          </SettingsRow>
          <SettingsRow title="Skip low-risk gates" desc="Auto-approve gates below 40% risk score">
            <Toggle on={darkGates} onToggle={() => setDarkGates((v) => !v)} />
          </SettingsRow>
          <SettingsRow title="Autonomy level" desc="How much freedom agents get between gates">
            <div className="flex gap-1.5">
              {['Cautious', 'Balanced', 'Bold'].map((o) => {
                const sel = autonomy === o
                return (
                  <button
                    key={o}
                    onClick={() => setAutonomy(o)}
                    className="rounded-lg px-3 py-1.5 text-[12px] font-semibold transition-colors"
                    style={{
                      backgroundColor: sel ? GOLD : CANVAS,
                      color: sel ? PLATINUM : MUTED,
                      border: `1px solid ${sel ? GOLD : HAIRLINE}`,
                    }}
                  >
                    {o}
                  </button>
                )
              })}
            </div>
          </SettingsRow>
        </div>
      </Card>

      {/* Notifications */}
      <Card className="mt-6 px-5 py-1">
        <div className="border-b py-3" style={{ borderColor: HAIRLINE }}>
          <span className="font-mono text-[11px] tracking-[0.12em]" style={{ color: GOLD }}>
            NOTIFICATIONS
          </span>
        </div>
        <div className="divide-y" style={{ borderColor: 'rgba(86,86,86,0.4)' }}>
          <SettingsRow title="Approval alerts" desc="Ping me when a gate needs human review">
            <Toggle on={notify} onToggle={() => setNotify((v) => !v)} />
          </SettingsRow>
          <SettingsRow title="Webhook endpoint" desc="POST cycle events to your service">
            <input
              defaultValue="https://api.theloop.io/hooks"
              className="w-56 rounded-lg border px-3 py-2 font-mono text-[12px] outline-none"
              style={{ backgroundColor: CANVAS, borderColor: HAIRLINE, color: PLATINUM }}
              onFocus={(e) => (e.currentTarget.style.borderColor = GOLD)}
              onBlur={(e) => (e.currentTarget.style.borderColor = HAIRLINE)}
            />
          </SettingsRow>
        </div>
      </Card>

      <div className="mt-6 flex justify-end gap-3">
        <button
          className="rounded-lg border px-5 py-2.5 text-[14px] font-semibold"
          style={{ borderColor: HAIRLINE, color: MUTED, backgroundColor: 'transparent' }}
        >
          Reset
        </button>
        <button
          onClick={handleSave}
          className="rounded-lg px-5 py-2.5 text-[14px] font-bold transition-transform hover:scale-105"
          style={{ backgroundColor: GOLD, color: PLATINUM, boxShadow: goldGlow }}
        >
          {saved ? 'Saved!' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}

/* ── App shell ───────────────────────────────────────────────────── */
export default function App() {
  const [nav, setNav] = useState<NavKey>('command')
  const [modalOpen, setModalOpen] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [cycleNumber, setCycleNumber] = useState(1)
  const [reviewData, setReviewData] = useState<any>(null)
  const [agentStatuses, setAgentStatuses] = useState<Record<string, string>>({
    researcher: 'awaiting',
    hook_writer: 'queued',
    script_writer: 'queued',
    designer: 'queued',
    publisher: 'queued',
    analyst: 'queued',
  })
  const [stats, setStats] = useState({ trends: 24, ideas: 18, hooks: 80, published: 42 })
  const [logs, setLogs] = useState<{ t: string; dot: string; text: string }[]>([
    { t: '22:45:10', dot: SUCCESS, text: 'Researcher completed cycle #1' },
    { t: '22:45:09', dot: GOLD, text: 'Pending human review at Gate 1' },
    { t: '22:44:52', dot: SUCCESS, text: 'Scored 24 trends · 8 high-urgency' },
    { t: '22:44:31', dot: DEEP, text: 'Compiling viral breakdown refs' },
    { t: '22:44:02', dot: SUCCESS, text: 'Ingested 1,204 signals' },
    { t: '22:43:40', dot: IDLE, text: 'Hook Writer queued' },
  ])

  const wsRef = useRef<WebSocket | null>(null)

  const addLog = (text: string, dot: string = SUCCESS) => {
    const t = new Date().toTimeString().slice(0, 8)
    setLogs((prev) => [{ t, dot, text }, ...prev].slice(0, 15))
  }

  // Simulated live log generator matching Figma design
  useEffect(() => {
    const extras = [
      { dot: GOLD, text: 'Recomputing viral scores' },
      { dot: SUCCESS, text: 'Cache warmed · 320ms' },
      { dot: DEEP, text: 'Awaiting operator input' },
    ]
    let i = 0
    const id = setInterval(() => {
      const t = new Date().toTimeString().slice(0, 8)
      const e = extras[i % extras.length]
      i++
      setLogs((prev) => [{ t, ...e }, ...prev].slice(0, 12))
    }, 4200)
    return () => clearInterval(id)
  }, [])

  // Connect WebSocket & REST
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host =
      window.location.port === '5173' || window.location.port === '8443' ? 'localhost:8000' : window.location.host
    const wsUrl = `${protocol}//${host}/ws`

    const connectWs = () => {
      try {
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => {
          setIsConnected(true)
          addLog('Connected to Noir Engine WebSocket', SUCCESS)
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'state_sync' && data.state) {
              setStats({
                trends: data.state.trends_count || 24,
                ideas: data.state.ideas_count || 18,
                hooks: data.state.hooks_count || 80,
                published: data.state.published_count || 42,
              })
            } else if (data.type === 'pipeline_started') {
              setIsRunning(true)
              setCycleNumber(data.cycle || 1)
              addLog(`Pipeline cycle #${data.cycle} started!`, GOLD)
            } else if (data.type === 'agent_started') {
              setAgentStatuses((prev) => ({ ...prev, [data.agent]: 'active' }))
              addLog(`${data.agent} is running...`, GOLD)
            } else if (data.type === 'approval_required') {
              setAgentStatuses((prev) => ({ ...prev, [data.agent]: 'awaiting' }))
              addLog(`Approval gate active: ${data.agent}`, GOLD)
              setReviewData({ agent: data.agent, title: 'Gate 01: Research & Trend Review', content: data.state })
              setModalOpen(true)
            } else if (data.type === 'pipeline_completed') {
              setIsRunning(false)
              addLog(`Cycle #${data.cycle} completed successfully!`, SUCCESS)
            }
          } catch (err) {
            console.error('WS parsing error:', err)
          }
        }

        ws.onclose = () => {
          setIsConnected(false)
          setTimeout(connectWs, 3000)
        }
      } catch (e) {
        setIsConnected(false)
      }
    }

    connectWs()

    // Poll status fallback
    const pollStatus = async () => {
      try {
        const res = await fetch(`http://${host}/api/pipeline/status`)
        const data = await res.json()
        if (data.agent_statuses) {
          const mapped: Record<string, string> = {}
          for (const [k, v] of Object.entries(data.agent_statuses)) {
            mapped[k] = v === 'active' || v === 'awaiting_approval' ? 'awaiting' : v === 'completed' ? 'completed' : 'queued'
          }
          setAgentStatuses((prev) => ({ ...prev, ...mapped }))
        }
        if (data.pipeline_running !== undefined) setIsRunning(data.pipeline_running)
        if (data.cycle_number) setCycleNumber(data.cycle_number)
      } catch (e) {
        // quiet
      }
    }

    pollStatus()
    const interval = setInterval(pollStatus, 6000)

    return () => {
      clearInterval(interval)
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  useEffect(() => {
    if (nav === 'approvals') {
      setModalOpen(true)
    }
  }, [nav])

  const handleStart = async () => {
    try {
      const host =
        window.location.port === '5173' || window.location.port === '8443' ? 'localhost:8000' : window.location.host
      const res = await fetch(`http://${host}/api/pipeline/start`, { method: 'POST' })
      const data = await res.json()
      if (data.status === 'started') {
        setIsRunning(true)
        addLog('Triggered pipeline cycle', GOLD)
      }
    } catch (e) {
      addLog('Failed to start pipeline: ' + String(e), DEEP)
    }
    setModalOpen(true)
  }

  const handleApprovalAction = async (action: string, feedback: string) => {
    try {
      const host =
        window.location.port === '5173' || window.location.port === '8443' ? 'localhost:8000' : window.location.host
      const formData = new FormData()
      formData.append('action', action)
      formData.append('feedback', feedback)

      const res = await fetch(`http://${host}/api/approve`, { method: 'POST', body: formData })
      const data = await res.json()
      if (data.status === 'processed') {
        addLog(`Approval processed: ${action}`, SUCCESS)
        setModalOpen(false)
        if (nav === 'approvals') setNav('command')
      }
    } catch (e) {
      addLog('Approval submit error: ' + String(e), DEEP)
      setModalOpen(false)
      if (nav === 'approvals') setNav('command')
    }
  }

  const handleInspectNode = (agentId: string) => {
    setReviewData({
      agent: agentId,
      title: `Gate Review: ${agentId.replace('_', ' ').toUpperCase()}`,
      content: {
        trends: DEFAULT_HOOKS.map((h) => ({ title: h.text, virality_score: h.score / 10, platform: h.tag })),
      },
    })
    setModalOpen(true)
  }

  return (
    <div className="flex h-screen w-full overflow-hidden" style={{ backgroundColor: CANVAS }}>
      <Sidebar
        active={nav}
        onNav={(k) => {
          setNav(k)
          if (k !== 'approvals') setModalOpen(false)
        }}
        hasPendingApproval={true}
        isConnected={isConnected}
      />

      <main className="flex-1 overflow-y-auto">
        {nav === 'analytics' ? (
          <AnalyticsView />
        ) : nav === 'settings' ? (
          <SettingsView />
        ) : (
          <CommandCenter
            stats={stats}
            agentStatuses={agentStatuses}
            isRunning={isRunning}
            cycleNumber={cycleNumber}
            logs={logs}
            onStart={handleStart}
            onInspectNode={handleInspectNode}
          />
        )}
      </main>

      {modalOpen && (
        <ApprovalModal
          onClose={() => {
            setModalOpen(false)
            if (nav === 'approvals') setNav('command')
          }}
          reviewData={reviewData}
          onAction={handleApprovalAction}
        />
      )}
    </div>
  )
}
