export const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })

export const formatTime = (iso: string) =>
  new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })

export const formatWindowEnd = (iso: string, _startIso?: string) => {
  if (!iso) return 'Unknown'
  const timeStr = formatTime(iso)
  if (timeStr === '00:00') {
    return '24:00'
  }
  return timeStr
}

export const formatDateTime = (iso: string) => `${formatDate(iso)} ${formatTime(iso)}`

export const formatHour = (h: number) => {
  const hh = Math.floor(h)
  const mm = Math.round((h - hh) * 60)
  return `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`
}

export const orUnknown = (v: string | null | undefined) => (v ? v : 'Unknown')
