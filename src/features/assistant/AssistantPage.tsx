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
      <PageHero title="AI Research Assistant" subtitle="Ask a question. Answers show their sources." chips={<Chip label="Mock data" color="var(--est)" />} scene={{ body: 'moon', mode: 'rise' }} />

      <div className="glass mx-auto flex min-h-[420px] max-w-3xl flex-col p-5">
        <div className="flex-1 space-y-4" aria-live="polite">
          {!msgs.length && <p className="py-10 text-center text-[var(--text-2)]">Try one of the example questions below.</p>}
          {msgs.map((m, i) =>
            m.role === 'user' ? (
              <div key={i} className="ml-auto max-w-[85%] rounded-[14px] bg-[var(--earth)]/15 px-4 py-3">{m.text}</div>
            ) : m.role === 'error' ? (
              <div key={i} className="max-w-[85%] rounded-[14px] border border-[var(--border)] px-4 py-3 text-[var(--blocked)]">Something went wrong: {m.text}</div>
            ) : (
              <div key={i} className="max-w-[90%] rounded-[14px] border border-[var(--border)] bg-white/[0.03] px-4 py-3">
                {m.a.no_evidence ? <p>Data not available for this question.</p> : (
                  <>
                    <p>{m.a.answer}</p>
                    <ul className="mt-3 space-y-2">
                      {m.a.statements.map((s, j) => (
                        <li key={j} className="flex items-start gap-2 text-sm">
                          <Chip label={s.kind === 'estimated' ? 'Estimated' : 'Measured'} color={s.kind === 'estimated' ? 'var(--est)' : 'var(--ok)'} />
                          <span className={s.kind === 'estimated' ? 'italic text-[var(--text-2)]' : ''}>{s.text}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {m.a.citations.map((c) => (
                        <button key={c.product_id} type="button" onClick={() => openDrawer(`source:${c.product_id}`)} className="rounded-full border border-[var(--border)] px-3 py-1 text-xs text-[var(--earth)] hover:border-[var(--border-hover)]">{c.label}</button>
                      ))}
                    </div>
                  </>
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
