import { create } from 'zustand'
import type { AssistantAnswer } from '../types'

export type AssistantMsg =
  | { role: 'user'; text: string }
  | { role: 'assistant'; a: AssistantAnswer }
  | { role: 'error'; text: string }

type UI = {
  drawerOpen: boolean
  drawerTarget: string | null
  openDrawer: (target: string) => void
  closeDrawer: () => void

  // Assistant Drawer State (persisted across page navigation in the session)
  assistantOpen: boolean
  openAssistant: () => void
  closeAssistant: () => void
  toggleAssistant: () => void
  assistantMessages: AssistantMsg[]
  setAssistantMessages: (msgs: AssistantMsg[] | ((prev: AssistantMsg[]) => AssistantMsg[])) => void
  clearAssistantMessages: () => void
}

export const useUI = create<UI>()((set) => ({
  drawerOpen: false,
  drawerTarget: null,
  openDrawer: (drawerTarget) => set({ drawerOpen: true, drawerTarget }),
  closeDrawer: () => set({ drawerOpen: false }),

  assistantOpen: false,
  openAssistant: () => set({ assistantOpen: true }),
  closeAssistant: () => set({ assistantOpen: false }),
  toggleAssistant: () => set((s) => ({ assistantOpen: !s.assistantOpen })),
  assistantMessages: [],
  setAssistantMessages: (msgs) =>
    set((s) => ({
      assistantMessages: typeof msgs === 'function' ? msgs(s.assistantMessages) : msgs,
    })),
  clearAssistantMessages: () => set({ assistantMessages: [] }),
}))

export type Role = 'Public' | 'Researcher' | 'Admin'
export function useRole(): Role {
  const r = new URLSearchParams(window.location.search).get('role')
  if (r === 'admin') return 'Admin'
  if (r === 'researcher') return 'Researcher'
  return 'Public'
}
