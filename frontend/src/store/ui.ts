import { create } from 'zustand'

type UI = {
  drawerOpen: boolean
  drawerTarget: string | null
  openDrawer: (target: string) => void
  closeDrawer: () => void
}

export const useUI = create<UI>()((set) => ({
  drawerOpen: false,
  drawerTarget: null,
  openDrawer: (drawerTarget) => set({ drawerOpen: true, drawerTarget }),
  closeDrawer: () => set({ drawerOpen: false }),
}))

export type Role = 'Public' | 'Researcher' | 'Admin'
export function useRole(): Role {
  const r = new URLSearchParams(window.location.search).get('role')
  if (r === 'admin') return 'Admin'
  if (r === 'researcher') return 'Researcher'
  return 'Public'
}
