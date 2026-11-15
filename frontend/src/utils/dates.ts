const DAY_MS = 86400000

export function toRange(date: string, endDate: string | null) {
  const start = new Date(`${date}T00:00:00Z`)
  const last = new Date(`${endDate ?? date}T00:00:00Z`)
  return { start: start.toISOString(), end: new Date(last.getTime() + DAY_MS).toISOString() }
}

export const daysBetween = (start: string, end: string) =>
  Math.max(1, Math.round((Date.parse(end) - Date.parse(start)) / DAY_MS))

export const addDaysIso = (iso: string, n: number) => new Date(Date.parse(iso) + n * DAY_MS).toISOString()
