import { useState, useRef, useEffect } from 'react'
import './App.css'

// ── Types ──────────────────────────────────────────────────────────────────
type EventType = 'tool_call' | 'tool_result' | 'text' | 'error' | 'session_id'

interface AgentEvent {
  type: EventType
  data: string | { name: string; args: Record<string, unknown> }
}

interface Message {
  role: 'user' | 'agent'
  events: AgentEvent[]
}

// ── Sub-components ─────────────────────────────────────────────────────────
function ToolCallBadge({ name, args }: { name: string; args: Record<string, unknown> }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="tool-call" onClick={() => setOpen(o => !o)}>
      <span className="tool-icon">⚙</span>
      <span className="tool-name">{name}</span>
      <span className="tool-toggle">{open ? '▲' : '▼'}</span>
      {open && (
        <pre className="tool-args">{JSON.stringify(args, null, 2)}</pre>
      )}
    </div>
  )
}

function ToolResultBadge({ data }: { data: string }) {
  const [open, setOpen] = useState(false)
  const preview = data.length > 80 ? data.slice(0, 80) + '…' : data
  return (
    <div className="tool-result" onClick={() => setOpen(o => !o)}>
      <span className="tool-icon">↩</span>
      <span className="tool-preview">{open ? data : preview}</span>
    </div>
  )
}

function EventBlock({ event }: { event: AgentEvent }) {
  if (event.type === 'tool_call') {
    const d = event.data as { name: string; args: Record<string, unknown> }
    return <ToolCallBadge name={d.name} args={d.args} />
  }
  if (event.type === 'tool_result') {
    return <ToolResultBadge data={event.data as string} />
  }
  if (event.type === 'text') {
    return <p className="agent-text">{event.data as string}</p>
  }
  if (event.type === 'error') {
    return <p className="agent-error">⚠ {event.data as string}</p>
  }
  return null
}

function MessageBubble({ msg }: { msg: Message }) {
  if (msg.role === 'user') {
    return (
      <div className="bubble user-bubble">
        {(msg.events[0]?.data as string) ?? ''}
      </div>
    )
  }
  return (
    <div className="bubble agent-bubble">
      {msg.events.map((ev, i) => <EventBlock key={i} event={ev} />)}
    </div>
  )
}

// ── Preview Panel ──────────────────────────────────────────────────────────
const PREVIEW_URL = '/preview/'

function PreviewPanel({ refreshKey }: { refreshKey: number }) {
  return (
    <div className="preview-panel">
      <div className="preview-toolbar">
        <span className="preview-dot green" />
        <span className="preview-dot yellow" />
        <span className="preview-dot red" />
        <span className="preview-url">{PREVIEW_URL}</span>
      </div>
      <iframe
        key={refreshKey}
        className="preview-iframe"
        src={PREVIEW_URL}
        title="Website Preview"
        sandbox="allow-scripts allow-same-origin allow-forms"
      />
    </div>
  )
}

// ── Main App ───────────────────────────────────────────────────────────────
export default function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID())
  const [showPreview, setShowPreview] = useState(false)
  const [previewKey, setPreviewKey] = useState(0)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Check if WorkingDirectory has an index.html on mount
  useEffect(() => {
    fetch('/api/preview/files')
      .then(r => r.json())
      .then(d => { if (d.has_index) setShowPreview(true) })
      .catch(() => {})
  }, [])

  async function sendMessage() {
    const prompt = input.trim()
    if (!prompt || loading) return

    setInput('')
    setLoading(true)

    // Add user message
    setMessages(prev => [...prev, { role: 'user', events: [{ type: 'text', data: prompt }] }])

    // Add empty agent message that we'll fill as events stream in
    setMessages(prev => [...prev, { role: 'agent', events: [] }])

    try {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, session_id: sessionId }),
      })

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        for (const line of chunk.split('\n')) {
          if (!line.startsWith('data: ')) continue
          const raw = line.replace('data: ', '').trim()
          if (raw === '[DONE]') break

          const event: AgentEvent = JSON.parse(raw)

          // session_id event: store it, don't display it
          if (event.type === 'session_id') {
            setSessionId(event.data as string)
            continue
          }

          setMessages(prev => {
            const updated = [...prev]
            const last = updated[updated.length - 1]
            updated[updated.length - 1] = {
              ...last,
              events: [...last.events, event],
            }
            return updated
          })
        }
      }
    } catch (e) {
      setMessages(prev => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        updated[updated.length - 1] = {
          ...last,
          events: [...last.events, { type: 'error', data: String(e) }],
        }
        return updated
      })
    } finally {
      setLoading(false)
      // Auto-refresh preview after the agent finishes (files may have changed)
      setPreviewKey(k => k + 1)
      // Re-check for index.html
      fetch('/api/preview/files')
        .then(r => r.json())
        .then(d => { if (d.has_index) setShowPreview(true) })
        .catch(() => {})
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className={`app-shell ${showPreview ? 'with-preview' : ''}`}>
      {/* ── Chat side ── */}
      <div className="layout">
        <header className="header">
          <div className="header-left">
            <div className="header-dot" />
            <span>WebDev Agent</span>
          </div>
          <div className="header-actions">
            <button
              className="download-btn"
              onClick={() => window.open('/api/download', '_blank')}
              title="Download project as ZIP"
            >
              📥 <span className="btn-label">Download</span>
            </button>
            <button
              className={`preview-toggle ${showPreview ? 'active' : ''}`}
              onClick={() => setShowPreview(p => !p)}
              title={showPreview ? 'Hide preview' : 'Show preview'}
            >
              {showPreview ? '◧' : '▣'}
              <span className="preview-toggle-label">
                {showPreview ? 'Hide Preview' : 'Show Preview'}
              </span>
            </button>
          </div>
        </header>

        <main className="chat-window">
          {messages.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">⬡</div>
              <p>Ask the agent anything about your codebase.</p>
            </div>
          )}
          {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}
          {loading && messages[messages.length - 1]?.events.length === 0 && (
            <div className="bubble agent-bubble">
              <span className="thinking">thinking<span className="dots" /></span>
            </div>
          )}
          <div ref={bottomRef} />
        </main>

        <footer className="input-bar">
          <textarea
            className="input"
            rows={1}
            placeholder="Ask the agent…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
          />
          <button
            className="send-btn"
            onClick={sendMessage}
            disabled={loading || !input.trim()}
          >
            {loading ? '…' : '↑'}
          </button>
        </footer>
      </div>

      {/* ── Preview side ── */}
      {showPreview && (
        <PreviewPanel refreshKey={previewKey} />
      )}
    </div>
  )
}
