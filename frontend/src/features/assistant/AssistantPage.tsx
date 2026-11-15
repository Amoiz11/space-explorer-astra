import { useRef, useState, type FormEvent } from 'react'
import { Send } from 'lucide-react'
import { askAssistant } from '../../services'
import { useUI } from '../../store/ui'
import type { AssistantAnswer } from '../../types'
import Chip from '../../components/Chip'
import PageHero from '../../components/PageHero'
import Skeleton from '../../components/Skeleton'

type Msg = { role: 'user'; text: string } | { role: 'assistant'; a: AssistantAnswer } | { role: 'error'; text: string }

const examples = ['How does sunlight work near the lunar south pole?', 'Is Earth visible from the Moon south pole?', 'Is Perseverance still active?']

export default function AssistantPage() {
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const openDrawer = useUI((u) => u.openDrawer)
  const end = useRef<HTMLDivElement>(null)

  const ask = async (q: string) => {
    if (!q.trim() || busy) return
    setMsgs((m) => [...m, { role: 'user', text: q }])
    setText('')
    setBusy(true)
    try {
      const a = await askAssistant(q)
      setMsgs((m) => [...m, { role: 'assistant', a }])
    } catch (e) {
      setMsgs((m) => [...m, { role: 'error', text: e instanceof Error ? e.message : 'Request failed' }])
    } finally {
      setBusy(false)
      setTimeout(() => end.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }
  }
  const submit = (e: FormEvent) => { e.preventDefault(); void ask(text) }

  return (
    <div className="space-y-6">
      <PageHero
        title="AI Research Assistant"
        subtitle="Ask a question. Answers show their sources."
        scene={{ body: 'moon', mode: 'rise' }}
      />

      <div className="glass mx-auto flex min-h-[420px] max-w-3xl flex-col p-5">
        <div className="flex-1 space-y-4" aria-live="polite">
          {!msgs.length && <p className="py-10 text-center text-[var(--text-2)]">Try one of the example questions below.</p>}
          {msgs.map((m, i) =>
            m.role === 'user' ? (
              <div key={i} className="ml-auto max-w-[85%] rounded-[14px] bg-[var(--earth)]/15 px-4 py-3">{m.text}</div>
            ) : m.role === 'error' ? (
              <div key={i} className="max-w-[85%] rounded-[14px] border border-[var(--blocked)]/40 bg-[var(--blocked)]/10 px-4 py-3 text-[var(--text-1)]">
                <span className="font-semibold text-[var(--blocked)]">Error: </span>
                {m.text}
              </div>
            ) : (
              <div key={i} className="max-w-[90%] space-y-3 rounded-[14px] border border-[var(--border)] bg-white/[0.03] px-4 py-3">
                <div className="flex items-center justify-between gap-2 border-b border-[var(--border)]/60 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-[var(--text-2)]">Response</span>
                    <Chip
                      label={m.a.answer_mode === 'llm' ? 'LLM grounded' : 'Template grounded'}
                      color={m.a.answer_mode === 'llm' ? 'var(--earth)' : 'var(--ok)'}
                    />
                  </div>
                  {m.a.llm_fallback_reason && (
                    <span className="mono text-[11px] text-[var(--text-2)]">mode: {m.a.llm_fallback_reason}</span>
                  )}
                </div>

                <div className="whitespace-pre-line text-sm leading-relaxed text-[var(--text-1)]">
                  {m.a.answer}
                </div>

                {m.a.citations && m.a.citations.length > 0 && (
                  <div className="space-y-1.5 pt-2">
                    <p className="text-xs font-medium text-[var(--text-2)]">Citations &amp; Sources</p>
                    <div className="flex flex-wrap gap-2">
                      {m.a.citations.map((c, j) => (
                        <button
                          key={j}
                          type="button"
                          onClick={() => openDrawer(`source:${c.product_id}`)}
                          className="flex items-center gap-2 rounded-full border border-[var(--border)] bg-white/[0.02] px-3 py-1 text-xs text-[var(--text-1)] hover:border-[var(--earth)] hover:text-[var(--earth)]"
                          title={`Product: ${c.product_id}`}
                        >
                          <span className="font-medium">{c.source_name}</span>
                          <span className="mono text-[10px] text-[var(--text-2)]">({c.label})</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {m.a.disclaimers && m.a.disclaimers.length > 0 && (
                  <div className="space-y-1 border-t border-[var(--border)]/40 pt-2 text-xs text-[var(--text-2)]">
                    {m.a.disclaimers.map((d, k) => (
                      <p key={k} className="italic">• {d}</p>
                    ))}
                  </div>
                )}
              </div>
            ),
          )}
          {busy && <Skeleton className="h-16 max-w-[60%]" />}
          <div ref={end} />
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {examples.map((q) => <button key={q} type="button" onClick={() => void ask(q)} className="rounded-full border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-2)] hover:border-[var(--border-hover)] hover:text-white">{q}</button>)}
        </div>
        <form onSubmit={submit} className="mt-3 flex gap-2">
          <input className="field" value={text} onChange={(e) => setText(e.target.value)} placeholder="Ask a question" aria-label="Your question" />
          <button type="submit" className="btn btn-primary" disabled={busy || !text.trim()} aria-label="Send"><Send size={16} /></button>
        </form>
      </div>
    </div>
  )
}
