import { useEffect, useRef, useState, type FormEvent } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Bot, Send, Sparkles, X } from 'lucide-react'
import { askAssistant } from '../services'
import { useUI, type AssistantMsg } from '../store/ui'
import Chip from './Chip'
import Skeleton from './Skeleton'
import Button from './Button'

const examples = [
  'How does sunlight work near the lunar south pole?',
  'Is Earth visible from the Moon south pole?',
  'Is Perseverance still active?',
]

export default function AssistantDrawer() {
  const { assistantOpen, closeAssistant, assistantMessages, setAssistantMessages, openDrawer, drawerOpen } = useUI()
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const closeBtnRef = useRef<HTMLButtonElement>(null)
  const drawerRef = useRef<HTMLElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Focus management and Escape key handling
  useEffect(() => {
    if (!assistantOpen) return

    // Focus input or close button when opened
    const timer = setTimeout(() => {
      inputRef.current?.focus()
    }, 100)

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        // If research drawer is open on top, let research drawer close first
        if (drawerOpen) return
        closeAssistant()
      }

      // Simple focus trap
      if (e.key === 'Tab' && drawerRef.current) {
        const focusable = drawerRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        if (!focusable.length) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      clearTimeout(timer)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [assistantOpen, closeAssistant, drawerOpen])

  // Scroll to bottom on new message
  useEffect(() => {
    if (assistantOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [assistantMessages, assistantOpen, busy])

  const ask = async (q: string) => {
    if (!q.trim() || busy) return
    const userMsg: AssistantMsg = { role: 'user', text: q.trim() }
    setAssistantMessages((prev) => [...prev, userMsg])
    setText('')
    setBusy(true)

    try {
      const a = await askAssistant(q.trim())
      setAssistantMessages((prev) => [...prev, { role: 'assistant', a }])
    } catch (e) {
      let errorMsg = e instanceof Error ? e.message : 'Request failed'
      if (errorMsg.includes('429')) {
        errorMsg = 'Rate limit exceeded (429). Please wait a moment before trying again.'
      } else if (errorMsg.includes('500')) {
        errorMsg = 'Internal server error (500). The service encountered an unexpected error.'
      }
      setAssistantMessages((prev) => [...prev, { role: 'error', text: errorMsg }])
    } finally {
      setBusy(false)
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }
  }

  const submit = (e: FormEvent) => {
    e.preventDefault()
    void ask(text)
  }

  return (
    <AnimatePresence>
      {assistantOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={closeAssistant}
            aria-hidden="true"
          />

          {/* Drawer Sheet */}
          <motion.aside
            ref={drawerRef}
            role="dialog"
            aria-modal="true"
            aria-label="AI Research Assistant"
            className="fixed right-0 top-0 bottom-0 z-40 flex h-full w-full sm:max-w-[420px] flex-col border-l border-white/10 bg-[var(--bg-0)]/95 shadow-[-10px_0_30px_rgba(0,0,0,0.6)] backdrop-blur-2xl"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 28, stiffness: 300 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/10 bg-white/[0.02] px-5 py-4">
              <div className="flex items-center gap-2.5">
                <span className="grid h-9 w-9 place-items-center rounded-xl border border-white/10 bg-[var(--earth)]/10 text-[var(--earth)]">
                  <Bot size={18} />
                </span>
                <div>
                  <h2 className="text-base font-semibold text-white">AI Research Assistant</h2>
                  <p className="text-xs text-[var(--text-2)]">Verified NASA scientific citations</p>
                </div>
              </div>
              <button
                ref={closeBtnRef}
                onClick={closeAssistant}
                aria-label="Close assistant"
                className="grid h-8 w-8 place-items-center rounded-lg border border-white/10 bg-white/5 text-[var(--text-2)] hover:border-white/20 hover:text-white"
              >
                <X size={16} />
              </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 space-y-4 overflow-y-auto p-4" aria-live="polite">
              {!assistantMessages.length && (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <span className="grid h-12 w-12 place-items-center rounded-2xl border border-white/10 bg-white/5 text-[var(--earth)] shadow-inner">
                    <Sparkles size={22} />
                  </span>
                  <h3 className="mt-4 text-base font-medium text-white">Ask Space Explorer AI</h3>
                  <p className="mt-1 max-w-[280px] text-xs text-[var(--text-2)]">
                    Ask questions about lunar landing sites, illumination windows, or Mars rover telemetry.
                  </p>

                  <div className="mt-6 flex flex-col gap-2 w-full">
                    <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-2)] text-left px-1">
                      Suggested Questions
                    </p>
                    {examples.map((q) => (
                      <button
                        key={q}
                        type="button"
                        onClick={() => void ask(q)}
                        className="rounded-xl border border-white/10 bg-white/[0.03] p-2.5 text-left text-xs text-[var(--text-1)] transition-colors hover:border-[var(--earth)]/40 hover:bg-white/[0.06]"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {assistantMessages.map((m, i) =>
                m.role === 'user' ? (
                  <div
                    key={i}
                    className="ml-auto max-w-[85%] rounded-[16px] border border-[var(--earth)]/25 bg-[var(--earth)]/15 px-4 py-3 text-sm text-white"
                  >
                    {m.text}
                  </div>
                ) : m.role === 'error' ? (
                  <div
                    key={i}
                    className="max-w-[90%] rounded-[16px] border border-[var(--blocked)]/40 bg-[var(--blocked)]/10 px-4 py-3 text-sm text-[var(--text-1)]"
                  >
                    <span className="font-semibold text-[var(--blocked)]">Error: </span>
                    {m.text}
                  </div>
                ) : (
                  <div
                    key={i}
                    className="max-w-[95%] space-y-3 rounded-[16px] border border-white/10 bg-white/[0.03] p-4 text-sm"
                  >
                    {/* Header badge */}
                    <div className="flex items-center justify-between gap-2 border-b border-white/10 pb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-[var(--text-2)]">Response</span>
                        <Chip
                          label={m.a.answer_mode === 'llm' ? 'LLM grounded' : 'Template grounded'}
                          color={m.a.answer_mode === 'llm' ? 'var(--earth)' : 'var(--ok)'}
                        />
                      </div>
                      {m.a.llm_fallback_reason && (
                        <span className="mono text-[10px] text-[var(--text-2)]">
                          mode: {m.a.llm_fallback_reason}
                        </span>
                      )}
                    </div>

                    {/* Answer text */}
                    <div className="whitespace-pre-line text-xs sm:text-sm leading-relaxed text-[var(--text-1)]">
                      {m.a.answer}
                    </div>

                    {/* Citations */}
                    {m.a.citations && m.a.citations.length > 0 && (
                      <div className="space-y-1.5 pt-2 border-t border-white/5">
                        <p className="text-[11px] font-medium text-[var(--text-2)]">Citations &amp; Sources</p>
                        <div className="flex flex-wrap gap-1.5">
                          {m.a.citations.map((c, j) => (
                            <button
                              key={j}
                              type="button"
                              onClick={() => openDrawer(`source:${c.product_id}`)}
                              className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-[var(--text-1)] hover:border-[var(--earth)] hover:text-[var(--earth)] transition-colors"
                              title={`Product ID: ${c.product_id}`}
                            >
                              <span className="font-medium">{c.source_name}</span>
                              <span className="mono text-[10px] text-[var(--text-2)]">({c.label})</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Disclaimers */}
                    {m.a.disclaimers && m.a.disclaimers.length > 0 && (
                      <div className="space-y-1 border-t border-white/5 pt-2 text-[11px] text-[var(--text-2)]">
                        {m.a.disclaimers.map((d, k) => (
                          <p key={k} className="italic">• {d}</p>
                        ))}
                      </div>
                    )}
                  </div>
                )
              )}

              {busy && (
                <div className="space-y-2 rounded-[16px] border border-white/10 bg-white/[0.02] p-4">
                  <div className="flex items-center gap-2 text-xs text-[var(--text-2)]">
                    <Sparkles size={14} className="animate-spin text-[var(--earth)]" />
                    <span>Consulting NASA planetary intelligence...</span>
                  </div>
                  <Skeleton className="h-4 w-4/5" />
                  <Skeleton className="h-4 w-3/5" />
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Footer */}
            <div className="border-t border-white/10 bg-white/[0.02] p-4">
              <form onSubmit={submit} className="flex gap-2">
                <input
                  ref={inputRef}
                  className="field flex-1 text-sm bg-white/[0.05] border-white/10 focus:border-[var(--earth)] rounded-xl px-3 py-2 text-white"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Ask a question..."
                  aria-label="Your question"
                  disabled={busy}
                />
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  disabled={busy || !text.trim()}
                  aria-label="Send"
                  className="!px-3.5"
                >
                  <Send size={15} />
                </Button>
              </form>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
