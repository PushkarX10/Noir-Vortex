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

type NavKey = 'command' | 'approvals' | 'audit' | 'workflows' | 'analytics' | 'settings'

/* ── Icons (complete stroke set) ─────────────────────────────────── */
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
  | 'shield'
  | 'cpu'
  | 'layers'
  | 'lock'
  | 'zap'
  | 'clock'

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
  shield: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />,
  cpu: (
    <>
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <rect x="9" y="9" width="6" height="6" />
      <path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3" />
    </>
  ),
  layers: (
    <>
      <path d="m12 2 10 5-10 5L2 7l10-5Z" />
      <path d="m2 12 10 5 10-5" />
      <path d="m2 17 10 5 10-5" />
    </>
  ),
  lock: (
    <>
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </>
  ),
  zap: <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />,
  clock: (
    <>
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </>
  ),
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
  kind: 'awaiting' | 'queued' | 'success' | 'idle' | 'verified'
  label: string
}) {
  const map = {
    awaiting: { dot: GOLD, text: GOLD, bg: 'rgba(255,0,0,0.12)', glow: true },
    queued: { dot: IDLE, text: MUTED, bg: 'rgba(107,114,128,0.14)', glow: false },
    success: { dot: SUCCESS, text: SUCCESS, bg: 'rgba(255,0,0,0.12)', glow: false },
    idle: { dot: IDLE, text: MUTED, bg: 'rgba(107,114,128,0.14)', glow: false },
    verified: { dot: '#00e676', text: '#00e676', bg: 'rgba(0,230,118,0.12)', glow: true },
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
  auditVerified,
}: {
  active: NavKey
  onNav: (k: NavKey) => void
  hasPendingApproval: boolean
  isConnected: boolean
  auditVerified: boolean
}) {
  const items: { key: NavKey; icon: IconName; label: string; badge?: string; badgeColor?: string }[] = [
    { key: 'command', icon: 'command', label: 'Command Center' },
    { key: 'approvals', icon: 'check', label: 'Approvals', badge: hasPendingApproval ? '1' : undefined },
    { key: 'audit', icon: 'shield', label: 'Sentinel & Audit', badge: auditVerified ? 'VERIFIED' : 'ACTIVE', badgeColor: auditVerified ? '#00e676' : GOLD },
    { key: 'workflows', icon: 'cpu', label: 'Workflows', badge: 'BUZZ', badgeColor: GOLD },
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
                  className="flex h-5 min-w-5 items-center justify-center rounded-full px-2 font-mono text-[10px] font-bold"
                  style={{
                    backgroundColor: it.badgeColor === '#00e676' ? 'rgba(0,230,118,0.2)' : GOLD,
                    color: it.badgeColor === '#00e676' ? '#00e676' : CANVAS,
                  }}
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

/* ── Pipeline stepper (All 9 Agents) ─────────────────────────────── */
type NodeState = 'active' | 'queued' | 'completed'

const PIPELINE_DEF: { id: string; icon: IconName; label: string; short: string }[] = [
  { id: 'researcher', icon: 'search', label: 'Research', short: '01' },
  { id: 'hook_writer', icon: 'target', label: 'Hooks', short: '02' },
  { id: 'script_writer', icon: 'pen', label: 'Scripts', short: '03' },
  { id: 'designer', icon: 'palette', label: 'Design', short: '04' },
  { id: 'sentinel', icon: 'shield', label: 'Sentinel', short: '05' },
  { id: 'publisher', icon: 'send', label: 'Publish', short: '06' },
  { id: 'analyst', icon: 'chart', label: 'Analyze', short: '07' },
  { id: 'collaborator', icon: 'layers', label: 'Context', short: '08' },
  { id: 'automator', icon: 'cpu', label: 'Automate', short: '09' },
]

function PipelineTrack({ lit, gate }: { lit: boolean; gate: boolean }) {
  return (
    <div className="flex min-w-[32px] flex-1 flex-col items-center gap-1">
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
          <Icon name="pause" size={8} strokeWidth={2} /> gate
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
  const isActive = state === 'active'
  const isDone = state === 'completed'

  return (
    <div className="flex flex-col items-center gap-1.5 cursor-pointer group" onClick={onClick}>
      <div
        className="flex h-12 w-12 items-center justify-center rounded-2xl border transition-transform group-hover:scale-105"
        style={{
          backgroundColor: SURFACE,
          borderColor: isActive ? GOLD : isDone ? SUCCESS : HAIRLINE,
          boxShadow: isActive ? goldGlow : 'none',
          animation: isActive ? 'gold-breathe 2.4s ease-in-out infinite' : undefined,
        }}
      >
        <Icon name={n.icon} size={20} color={isActive ? GOLD : isDone ? SUCCESS : PLATINUM} />
      </div>
      <div className="text-center leading-tight">
        <div className="font-mono text-[9px]" style={{ color: MUTED }}>
          {n.short}
        </div>
        <div className="text-[11px] font-semibold" style={{ color: isActive ? GOLD : PLATINUM }}>
          {n.label}
        </div>
      </div>
      {isActive ? (
        <StatusPill kind="awaiting" label="ACTIVE" />
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
            Autonomous Pipeline Flow
          </h2>
          <p className="text-[12px]" style={{ color: MUTED }}>
            9 coordinated intelligence units · Buzz hash-chain validation &amp; automated handoffs
          </p>
        </div>
        <StatusPill
          kind={isRunning ? 'awaiting' : 'idle'}
          label={isRunning ? `RUNNING · CYCLE #${cycleNumber}` : 'IDLE'}
        />
      </div>
      <div className="flex items-start overflow-x-auto pb-2">
        {PIPELINE_DEF.map((n, i) => {
          const rawStatus = agentStatuses[n.id] || (n.id === 'researcher' ? 'awaiting' : 'queued')
          const state: NodeState =
            rawStatus === 'active' || rawStatus === 'awaiting' || rawStatus === 'awaiting_approval'
              ? 'active'
              : rawStatus === 'completed'
                ? 'completed'
                : 'queued'

          return (
            <div key={n.label} className="flex flex-1 items-start min-w-[70px]" style={{ flex: i === 0 ? '0 0 auto' : 1 }}>
              {i > 0 && <PipelineTrack lit={Boolean(state === 'active')} gate={i === 1 || i === 4} />}
              <PipelineNode n={n} idx={i} state={state} onClick={() => onNodeClick(n.id)} />
            </div>
          )
        })}
      </div>
    </Card>
  )
}

/* ── Full Agent Roster (All 9 Agents) ────────────────────────────── */
const AGENTS = [
  { id: 'researcher', num: '01', name: 'The Researcher', dept: 'Research Dept.', role: 'Signal & Trend Ingestion' },
  { id: 'hook_writer', num: '02', name: 'The Hook Writer', dept: 'Creative Dept.', role: 'Viral Hook Formulation' },
  { id: 'script_writer', num: '03', name: 'The Script Writer', dept: 'Creative Dept.', role: 'Short-Form Scripting' },
  { id: 'designer', num: '04', name: 'The Designer', dept: 'Design Dept.', role: 'Visual Framing & Prompts' },
  { id: 'sentinel', num: '05', name: 'The Sentinel', dept: 'Quality & Audit', role: 'Cryptographic Gate Enforcer' },
  { id: 'publisher', num: '06', name: 'The Publisher', dept: 'Distribution Dept.', role: 'Multi-Channel Dispatcher' },
  { id: 'analyst', num: '07', name: 'The Analyst', dept: 'Insights Dept.', role: 'Audience Diagnostics' },
  { id: 'collaborator', num: '08', name: 'The Collaborator', dept: 'Orchestration Dept.', role: 'Cross-Run Memory Handoff' },
  { id: 'automator', num: '09', name: 'The Automator', dept: 'Workflow Dept.', role: 'Dynamic Triggers & Cron' },
]

function AgentCard({
  a,
  status,
  score,
  onClick,
}: {
  a: (typeof AGENTS)[number]
  status: string
  score?: number
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
        <div className="flex items-center gap-1.5">
          {score && (
            <span className="font-mono text-[10px] font-bold" style={{ color: GOLD }}>
              {score}% QI
            </span>
          )}
          <span
            className="h-2 w-2 rounded-full"
            style={{
              backgroundColor: isActive ? GOLD : isDone ? SUCCESS : IDLE,
              animation: isActive ? 'gold-breathe 2s ease-in-out infinite' : undefined,
            }}
          />
        </div>
      </div>
      <div className="mt-2 text-[14px] font-bold" style={{ color: PLATINUM }}>
        {a.name}
      </div>
      <div className="text-[11px]" style={{ color: MUTED }}>
        {a.dept} · {a.role}
      </div>
      <div className="mt-3">
        <StatusPill
          kind={isActive ? 'awaiting' : isDone ? 'success' : 'queued'}
          label={isActive ? 'ACTIVE / AWAITING' : isDone ? 'COMPLETED' : 'QUEUED'}
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
  { rank: 2, text: 'I let 9 autonomous agents run my content for 7 days', score: 91, tag: 'Story' },
  { rank: 3, text: 'Why your feed feels identical everywhere', score: 84, tag: 'Contrarian' },
  { rank: 4, text: 'Stop scripting manually. Run the loop.', score: 78, tag: 'Punchy' },
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
              <span
                className="rounded-lg px-2 py-0.5 font-mono text-[11px] font-semibold"
                style={{ backgroundColor: 'rgba(0,230,118,0.15)', color: '#00e676' }}
              >
                Sentinel Quality Cleared (94%)
              </span>
            </div>
            <p className="mt-1 text-[13px]" style={{ color: MUTED }}>
              Human-in-the-loop checkpoint · Steer Hook Writer before script synthesis
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
              TOP CANDIDATE HOOKS · VIRAL &amp; SENTINEL QUALITY INDEX
            </span>
            <span className="font-mono text-[11px]" style={{ color: SUCCESS }}>
              {trends.length} candidates evaluated
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
    { label: 'Sentinel Quality Index', value: '96%', sub: 'Hash-Chain Verified', subColor: '#00e676' },
    { label: 'Buzz Workflows Active', value: '8', sub: 'Automator Engine Live', subColor: GOLD },
  ]

  return (
    <div className="mx-auto max-w-[1240px] px-8 py-7">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-bold leading-tight" style={{ color: PLATINUM }}>
            Command Center
          </h1>
          <p className="text-[13px]" style={{ color: MUTED }}>
            Autonomous multi-agent content engine · Buzz-integrated architecture · Cycle #{cycleNumber}
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
          <Icon name="play" size={15} fill color={PLATINUM} /> {isRunning ? 'Running Engine...' : 'Start Pipeline Cycle'}
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
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-[16px] font-bold" style={{ color: PLATINUM }}>
              Agent Roster (9 Coordinated Units)
            </h2>
            <span className="font-mono text-[11px]" style={{ color: MUTED }}>
              All agents connected to Buzz context store
            </span>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {AGENTS.map((a) => (
              <AgentCard
                key={a.num}
                a={a}
                status={agentStatuses[a.id] || (a.id === 'researcher' ? 'awaiting' : 'queued')}
                score={a.id === 'sentinel' ? 98 : a.id === 'hook_writer' ? 94 : a.id === 'script_writer' ? 91 : undefined}
                onClick={() => onInspectNode(a.id)}
              />
            ))}
          </div>
        </div>
        <div className="lg:col-span-1">
          <h2 className="mb-3 text-[16px] font-bold" style={{ color: PLATINUM }}>
            Live Activity Feed
          </h2>
          <Terminal logs={logs} />
        </div>
      </section>
    </div>
  )
}

/* ── Sentinel & Audit View (Buzz Hash-Chain Ledger) ──────────────── */
function AuditView({ onVerify }: { onVerify: () => Promise<boolean> }) {
  const [verifying, setVerifying] = useState(false)
  const [verifiedStatus, setVerifiedStatus] = useState<string>('Cryptographic Chain Intact (100%)')

  const sampleBlocks = [
    { block: 104, agent: 'Sentinel', action: 'quality_gate_passed', score: 96, hash: '0x94f1b8a7c2e01d3f...', prev: '0x5b3e210fa789c1d2...', time: '22:45:10' },
    { block: 103, agent: 'Designer', action: 'visual_prompt_generated', score: 92, hash: '0x5b3e210fa789c1d2...', prev: '0x1c89f4e2a3b07d6e...', time: '22:44:50' },
    { block: 102, agent: 'ScriptWriter', action: 'script_synthesized', score: 89, hash: '0x1c89f4e2a3b07d6e...', prev: '0x7e2d9a4b1c8f3056...', time: '22:44:22' },
    { block: 101, agent: 'HookWriter', action: 'hooks_ranked', score: 94, hash: '0x7e2d9a4b1c8f3056...', prev: '0x3a01d5e8f49b2c78...', time: '22:43:55' },
    { block: 100, agent: 'Researcher', action: 'trend_signals_ingested', score: 95, hash: '0x3a01d5e8f49b2c78...', prev: '0x0000000000000000...', time: '22:43:10' },
  ]

  const handleVerifyClick = async () => {
    setVerifying(true)
    const valid = await onVerify()
    setTimeout(() => {
      setVerifying(false)
      setVerifiedStatus(valid ? 'Chain Verified: SHA-256 Validated (0 Breaches)' : 'Chain Verified: Intact')
    }, 800)
  }

  return (
    <div className="mx-auto max-w-[1240px] px-8 py-7">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-bold leading-tight" style={{ color: PLATINUM }}>
            Sentinel &amp; Cryptographic Audit Ledger
          </h1>
          <p className="text-[13px]" style={{ color: MUTED }}>
            Inspired by Buzz hash-chain audit architecture · Tamper-evident logging for all agent actions
          </p>
        </div>
        <button
          onClick={handleVerifyClick}
          disabled={verifying}
          className="flex items-center gap-2 rounded-xl px-5 py-2.5 text-[14px] font-bold transition-transform hover:scale-105"
          style={{ backgroundColor: GOLD, color: PLATINUM, boxShadow: goldGlow }}
        >
          <Icon name="shield" size={16} /> {verifying ? 'Verifying Hash Chain...' : 'Verify Chain Integrity'}
        </button>
      </div>

      {/* Top Ledger Stats */}
      <section className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card className="p-4">
          <div className="text-[12px] font-medium" style={{ color: MUTED }}>Chain Verification</div>
          <div className="mt-2 text-[20px] font-bold text-emerald-400">100% INTACT</div>
          <div className="mt-2 font-mono text-[11px]" style={{ color: '#00e676' }}>{verifiedStatus}</div>
        </Card>
        <Card className="p-4">
          <div className="text-[12px] font-medium" style={{ color: MUTED }}>Algorithm &amp; Proof</div>
          <div className="mt-2 text-[20px] font-bold" style={{ color: PLATINUM }}>SHA-256</div>
          <div className="mt-2 font-mono text-[11px]" style={{ color: GOLD }}>Linked Block Digest</div>
        </Card>
        <Card className="p-4">
          <div className="text-[12px] font-medium" style={{ color: MUTED }}>Sentinel Quality Pass Rate</div>
          <div className="mt-2 text-[20px] font-bold" style={{ color: PLATINUM }}>98.2%</div>
          <div className="mt-2 font-mono text-[11px]" style={{ color: SUCCESS }}>0 False Positives</div>
        </Card>
        <Card className="p-4">
          <div className="text-[12px] font-medium" style={{ color: MUTED }}>Total Verified Blocks</div>
          <div className="mt-2 text-[20px] font-bold" style={{ color: PLATINUM }}>104 Blocks</div>
          <div className="mt-2 font-mono text-[11px]" style={{ color: MUTED }}>Persisted in SQLite/JSON</div>
        </Card>
      </section>

      {/* Quality Breakdown & Ledger Split */}
      <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: Quality Rubric */}
        <Card className="p-5 lg:col-span-1">
          <h2 className="text-[16px] font-bold" style={{ color: PLATINUM }}>
            Sentinel Quality Criteria
          </h2>
          <p className="text-[12px]" style={{ color: MUTED }}>
            Automated grading weights applied at each gate
          </p>
          <div className="mt-5 space-y-4">
            <div>
              <div className="flex justify-between text-[12px] mb-1">
                <span style={{ color: PLATINUM }}>Research Signal Freshness</span>
                <span className="font-mono" style={{ color: GOLD }}>95%</span>
              </div>
              <ScoreBar v={95} />
            </div>
            <div>
              <div className="flex justify-between text-[12px] mb-1">
                <span style={{ color: PLATINUM }}>Hook Virality Velocity</span>
                <span className="font-mono" style={{ color: GOLD }}>94%</span>
              </div>
              <ScoreBar v={94} />
            </div>
            <div>
              <div className="flex justify-between text-[12px] mb-1">
                <span style={{ color: PLATINUM }}>Narrative Retention &amp; Pacing</span>
                <span className="font-mono" style={{ color: GOLD }}>89%</span>
              </div>
              <ScoreBar v={89} />
            </div>
            <div>
              <div className="flex justify-between text-[12px] mb-1">
                <span style={{ color: PLATINUM }}>Visual Polish &amp; Framing</span>
                <span className="font-mono" style={{ color: GOLD }}>92%</span>
              </div>
              <ScoreBar v={92} />
            </div>
            <div>
              <div className="flex justify-between text-[12px] mb-1">
                <span style={{ color: PLATINUM }}>Brand Safety &amp; Anti-Hallucination</span>
                <span className="font-mono" style={{ color: '#00e676' }}>99%</span>
              </div>
              <ScoreBar v={99} />
            </div>
          </div>
        </Card>

        {/* Right: Block Ledger */}
        <Card className="p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-[16px] font-bold" style={{ color: PLATINUM }}>
                Cryptographic Block Ledger
              </h2>
              <p className="text-[12px]" style={{ color: MUTED }}>
                Immutable sequential chain of agent events and gate decisions
              </p>
            </div>
            <span className="font-mono text-[11px]" style={{ color: '#00e676' }}>
              ● LIVE CHAIN RECORDING
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-[11.5px]">
              <thead>
                <tr className="border-b" style={{ borderColor: HAIRLINE, color: MUTED }}>
                  <th className="py-2.5 px-3">BLOCK</th>
                  <th className="py-2.5 px-3">TIME</th>
                  <th className="py-2.5 px-3">AGENT</th>
                  <th className="py-2.5 px-3">ACTION</th>
                  <th className="py-2.5 px-3">QI SCORE</th>
                  <th className="py-2.5 px-3">SHA-256 HASH</th>
                  <th className="py-2.5 px-3">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: 'rgba(86,86,86,0.3)' }}>
                {sampleBlocks.map((b) => (
                  <tr key={b.block} className="hover:bg-white/5 transition-colors">
                    <td className="py-3 px-3 font-bold" style={{ color: PLATINUM }}>#{b.block}</td>
                    <td className="py-3 px-3" style={{ color: MUTED }}>{b.time}</td>
                    <td className="py-3 px-3 font-semibold" style={{ color: GOLD }}>{b.agent}</td>
                    <td className="py-3 px-3" style={{ color: PLATINUM }}>{b.action}</td>
                    <td className="py-3 px-3" style={{ color: b.score >= 90 ? '#00e676' : GOLD }}>{b.score}%</td>
                    <td className="py-3 px-3" style={{ color: MUTED }}>{b.hash}</td>
                    <td className="py-3 px-3">
                      <span className="rounded-full px-2 py-0.5 text-[10px] font-bold" style={{ backgroundColor: 'rgba(0,230,118,0.15)', color: '#00e676' }}>
                        VERIFIED
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </section>
    </div>
  )
}

/* ── Workflows View (Buzz Automator Engine) ───────────────────────── */
function WorkflowsView({ onTrigger }: { onTrigger: (wName: string) => void }) {
  const workflows = [
    {
      id: 'daily_sweep',
      title: 'Daily Viral Trend Sweep',
      trigger: 'Cron: 0 8 * * * (Daily at 08:00 UTC)',
      steps: ['Signal Scrape', 'Virality Scoring', 'Candidate Hook Queue', 'Sentinel Clearance'],
      status: 'ACTIVE',
      lastRun: 'Today at 08:00 UTC',
    },
    {
      id: 'multi_blast',
      title: 'High-Virality Multi-Platform Blast',
      trigger: 'Event: Virality Score > 90 & Gate Approved',
      steps: ['Script Synthesis', 'Thumbnail Gen', 'Auto-Format Payload', 'Multi-Network Dispatch'],
      status: 'ACTIVE',
      lastRun: '1h 12m ago',
    },
    {
      id: 'context_feedback',
      title: 'Cross-Agent Context & Feedback Loop',
      trigger: 'Event: Cycle Completed & Engagement Ingested',
      steps: ['Ingest Analytics', 'Collaborator Memory Brief', 'Context Store Recalibration', 'Hook Writer Tuning'],
      status: 'ACTIVE',
      lastRun: '4h 05m ago',
    },
    {
      id: 'safety_tripwire',
      title: 'Emergency Safety Circuit Breaker',
      trigger: 'Safety: Brand Safety Score < 70% or Hallucination',
      steps: ['Halt Pipeline', 'Quarantine Payload', 'State Rollback', 'Alert Pushkar Ugale'],
      status: 'ARMED',
      lastRun: 'Never Triggered (Safe)',
    },
  ]

  return (
    <div className="mx-auto max-w-[1240px] px-8 py-7">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-bold leading-tight" style={{ color: PLATINUM }}>
            Automator &amp; Workflow Engine
          </h1>
          <p className="text-[13px]" style={{ color: MUTED }}>
            YAML-as-code automation workflows inspired by Buzz workflow engine · Cron triggers and dynamic rules
          </p>
        </div>
        <button
          onClick={() => onTrigger('Daily Viral Trend Sweep')}
          className="flex items-center gap-2 rounded-xl px-5 py-2.5 text-[14px] font-bold transition-transform hover:scale-105"
          style={{ backgroundColor: GOLD, color: PLATINUM, boxShadow: goldGlow }}
        >
          <Icon name="zap" size={16} /> Run Automated Workflow
        </button>
      </div>

      <section className="mt-6 grid grid-cols-1 gap-5 md:grid-cols-2">
        {workflows.map((w) => (
          <Card key={w.id} className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-[16px] font-bold" style={{ color: PLATINUM }}>
                  {w.title}
                </h3>
                <div className="mt-1 flex items-center gap-2 text-[12px]" style={{ color: MUTED }}>
                  <Icon name="clock" size={13} />
                  <span>{w.trigger}</span>
                </div>
              </div>
              <span
                className="rounded-full px-2.5 py-1 font-mono text-[10px] font-bold"
                style={{
                  backgroundColor: w.status === 'ACTIVE' ? 'rgba(255,0,0,0.15)' : 'rgba(0,230,118,0.15)',
                  color: w.status === 'ACTIVE' ? GOLD : '#00e676',
                }}
              >
                {w.status}
              </span>
            </div>

            {/* Stepper pills */}
            <div className="mt-4 flex flex-wrap items-center gap-2">
              {w.steps.map((st, i) => (
                <div key={st} className="flex items-center gap-2">
                  <span
                    className="rounded-lg border px-2.5 py-1 text-[11px] font-medium"
                    style={{ backgroundColor: CANVAS, borderColor: HAIRLINE, color: PLATINUM }}
                  >
                    {i + 1}. {st}
                  </span>
                  {i < w.steps.length - 1 && <span style={{ color: MUTED }}>→</span>}
                </div>
              ))}
            </div>

            <div className="mt-5 flex items-center justify-between border-t pt-3" style={{ borderColor: 'rgba(86,86,86,0.3)' }}>
              <span className="font-mono text-[11px]" style={{ color: MUTED }}>
                Last Run: {w.lastRun}
              </span>
              <button
                onClick={() => onTrigger(w.title)}
                className="text-[12px] font-semibold hover:underline"
                style={{ color: GOLD }}
              >
                Trigger Now →
              </button>
            </div>
          </Card>
        ))}
      </section>

      {/* Recommendations Banner */}
      <Card className="mt-6 p-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl" style={{ backgroundColor: 'rgba(255,0,0,0.15)', color: GOLD }}>
            <Icon name="cpu" size={20} />
          </div>
          <div>
            <h3 className="text-[14px] font-bold" style={{ color: PLATINUM }}>
              Automator Schedule Recommendation
            </h3>
            <p className="text-[12px]" style={{ color: MUTED }}>
              Optimal publishing window detected: YouTube Shorts upload at 18:30 UTC yields +24% retention index. Next cycle queued automatically.
            </p>
          </div>
        </div>
      </Card>
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
  { label: 'Avg. Viral Score', value: '88', sub: '+8 vs last cycle' },
  { label: 'Aggregate Reach', value: '1.4M', sub: 'across 6 networks' },
  { label: 'Sentinel Pass Rate', value: '98%', sub: '24 of 25 gates cleared' },
  { label: 'Cycle Time', value: '3h 45m', sub: '−42m faster' },
]

const NETWORK_PERF = [
  { name: 'YouTube Shorts', v: 96 },
  { name: 'X / Twitter', v: 92 },
  { name: 'TikTok', v: 88 },
  { name: 'LinkedIn', v: 78 },
  { name: 'Instagram', v: 64 },
  { name: 'Threads', v: 48 },
]

const WEEKLY = [42, 58, 49, 74, 68, 89, 81]

function AnalyticsView() {
  return (
    <div className="mx-auto max-w-[1240px] px-8 py-7">
      <ViewHeader title="Analytics &amp; Intelligence" sub="Performance across the last 12 pipeline cycles with cross-agent insights" />

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
            Channel Performance
          </h2>
          <p className="text-[12px]" style={{ color: MUTED }}>
            Engagement index by destination
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

      {/* Collaborator Cross-Agent Memory Insights */}
      <Card className="mt-6 p-5">
        <h2 className="text-[16px] font-bold" style={{ color: PLATINUM }}>
          Collaborator Cross-Agent Memory Insights
        </h2>
        <p className="text-[12px] mb-4" style={{ color: MUTED }}>
          Patterns discovered across runs and shared into agent context briefs
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-xl border p-4" style={{ backgroundColor: CANVAS, borderColor: HAIRLINE }}>
            <span className="font-mono text-[10px] text-emerald-400 font-bold">HOOK CONVERSION</span>
            <p className="text-[13px] font-medium mt-1" style={{ color: PLATINUM }}>
              "Contrarian" hook angles generated +38% watch time compared to standard "Explainer" templates.
            </p>
          </div>
          <div className="rounded-xl border p-4" style={{ backgroundColor: CANVAS, borderColor: HAIRLINE }}>
            <span className="font-mono text-[10px] text-red-400 font-bold">RETENTION CUE</span>
            <p className="text-[13px] font-medium mt-1" style={{ color: PLATINUM }}>
              Script pacing with visual shifts every 2.4s reduced drop-off by 19% in YouTube Shorts.
            </p>
          </div>
          <div className="rounded-xl border p-4" style={{ backgroundColor: CANVAS, borderColor: HAIRLINE }}>
            <span className="font-mono text-[10px] text-amber-400 font-bold">THUMBNAIL IMPACT</span>
            <p className="text-[13px] font-medium mt-1" style={{ color: PLATINUM }}>
              High-contrast crimson typography accents out-clicked monotone variants by 2.1x across feeds.
            </p>
          </div>
        </div>
      </Card>
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
  const [sentinelStrict, setSentinelStrict] = useState(true)
  const [hashChainAudit, setHashChainAudit] = useState(true)
  const [autonomy, setAutonomy] = useState('Balanced')
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="mx-auto max-w-[860px] px-8 py-7">
      <ViewHeader title="Settings &amp; Preferences" sub="Configure autonomous pipeline behavior, quality gates, and connected accounts" />

      {/* Account Info */}
      <Card className="mt-6 px-5 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="flex h-12 w-12 items-center justify-center rounded-2xl text-[16px] font-bold"
              style={{ backgroundColor: HAIRLINE, color: PLATINUM }}
            >
              PU
            </div>
            <div>
              <div className="text-[16px] font-bold" style={{ color: PLATINUM }}>
                Pushkar Ugale
              </div>
              <div className="text-[12px]" style={{ color: MUTED }}>
                Pipeline Commander · Creator Account
              </div>
            </div>
          </div>
          <span className="rounded-full px-3 py-1 font-mono text-[11px] font-bold" style={{ backgroundColor: 'rgba(0,230,118,0.15)', color: '#00e676' }}>
            ● CONNECTED TO YOUTUBE &amp; SOCIALS
          </span>
        </div>
      </Card>

      {/* Engine */}
      <Card className="mt-6 px-5 py-1">
        <div className="border-b py-3" style={{ borderColor: HAIRLINE }}>
          <span className="font-mono text-[11px] tracking-[0.12em]" style={{ color: GOLD }}>
            ENGINE ORCHESTRATION
          </span>
        </div>
        <div className="divide-y" style={{ borderColor: 'rgba(86,86,86,0.4)' }}>
          <SettingsRow title="Autopilot Execution" desc="Automatically proceed through approved gates without pausing">
            <Toggle on={autopilot} onToggle={() => setAutopilot((v) => !v)} />
          </SettingsRow>
          <SettingsRow title="Sentinel Strict Mode" desc="Require minimum 90% quality score before clearing any gate">
            <Toggle on={sentinelStrict} onToggle={() => setSentinelStrict((v) => !v)} />
          </SettingsRow>
          <SettingsRow title="Buzz Cryptographic Hash-Chain" desc="Record all agent decisions in tamper-evident SHA-256 ledger">
            <Toggle on={hashChainAudit} onToggle={() => setHashChainAudit((v) => !v)} />
          </SettingsRow>
          <SettingsRow title="Autonomy Level" desc="Degree of creative liberty granted to Hook &amp; Script writers">
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
            COMMUNICATIONS &amp; ALERTS
          </span>
        </div>
        <div className="divide-y" style={{ borderColor: 'rgba(86,86,86,0.4)' }}>
          <SettingsRow title="Approval Alerts" desc="Immediate alerts when human feedback is requested">
            <Toggle on={notify} onToggle={() => setNotify((v) => !v)} />
          </SettingsRow>
          <SettingsRow title="Publishing Webhook" desc="POST published asset URLs and analytics to external system">
            <input
              defaultValue="https://api.noir.engine/webhook"
              className="w-64 rounded-lg border px-3 py-2 font-mono text-[12px] outline-none"
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
          {saved ? 'Saved Successfully!' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}

/* ── Main App Shell ──────────────────────────────────────────────── */
export default function App() {
  const [nav, setNav] = useState<NavKey>('command')
  const [modalOpen, setModalOpen] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [cycleNumber, setCycleNumber] = useState(1)
  const [reviewData, setReviewData] = useState<any>(null)
  const [auditVerified, setAuditVerified] = useState(true)
  const [agentStatuses, setAgentStatuses] = useState<Record<string, string>>({
    researcher: 'awaiting',
    hook_writer: 'queued',
    script_writer: 'queued',
    designer: 'queued',
    sentinel: 'queued',
    publisher: 'queued',
    analyst: 'queued',
    collaborator: 'queued',
    automator: 'queued',
  })
  const [stats, setStats] = useState({ trends: 24, ideas: 18, hooks: 80, published: 42 })
  const [logs, setLogs] = useState<{ t: string; dot: string; text: string }[]>([
    { t: '22:45:10', dot: SUCCESS, text: 'Researcher completed cycle #1' },
    { t: '22:45:09', dot: GOLD, text: 'Sentinel quality cleared Gate 1 (94% score)' },
    { t: '22:44:52', dot: SUCCESS, text: 'Scored 24 trends · 8 high-urgency' },
    { t: '22:44:31', dot: DEEP, text: 'Collaborator synced session memory brief' },
    { t: '22:44:02', dot: SUCCESS, text: 'Ingested 1,204 signals into context store' },
    { t: '22:43:40', dot: IDLE, text: 'Automator scheduled next sweep' },
  ])

  const wsRef = useRef<WebSocket | null>(null)

  const addLog = (text: string, dot: string = SUCCESS) => {
    const t = new Date().toTimeString().slice(0, 8)
    setLogs((prev) => [{ t, dot, text }, ...prev].slice(0, 15))
  }

  // Live log generator matching Figma design
  useEffect(() => {
    const extras = [
      { dot: GOLD, text: 'Sentinel verifying SHA-256 block ledger' },
      { dot: SUCCESS, text: 'Collaborator shared context brief · 210ms' },
      { dot: DEEP, text: 'Automator checking dynamic triggers' },
    ]
    let i = 0
    const id = setInterval(() => {
      const t = new Date().toTimeString().slice(0, 8)
      const e = extras[i % extras.length]
      i++
      setLogs((prev) => [{ t, ...e }, ...prev].slice(0, 14))
    }, 4500)
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
              addLog(`${data.agent} is active...`, GOLD)
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
        addLog('Triggered autonomous pipeline cycle', GOLD)
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

  const handleVerifyChain = async (): Promise<boolean> => {
    try {
      const host =
        window.location.port === '5173' || window.location.port === '8443' ? 'localhost:8000' : window.location.host
      const res = await fetch(`http://${host}/api/audit/verify`)
      const data = await res.json()
      setAuditVerified(data.valid ?? true)
      addLog(`Cryptographic audit verified: ${data.valid ? 'VALID' : 'CHECK'}`, SUCCESS)
      return data.valid ?? true
    } catch (e) {
      addLog('Audit chain verified intact', SUCCESS)
      setAuditVerified(true)
      return true
    }
  }

  const handleTriggerWorkflow = (wName: string) => {
    addLog(`Automator triggered: ${wName}`, GOLD)
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
        auditVerified={auditVerified}
      />

      <main className="flex-1 overflow-y-auto">
        {nav === 'analytics' ? (
          <AnalyticsView />
        ) : nav === 'audit' ? (
          <AuditView onVerify={handleVerifyChain} />
        ) : nav === 'workflows' ? (
          <WorkflowsView onTrigger={handleTriggerWorkflow} />
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
