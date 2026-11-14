import type { ReactNode } from 'react'

export type Column<T> = { header: string; cell: (row: T) => ReactNode; align?: 'right' }

export default function WindowsTable<T>({ rows, columns, empty }: { rows: T[]; columns: Column<T>[]; empty: string }) {
  if (!rows.length) return <p className="py-3 text-sm text-[var(--text-2)]">{empty}</p>
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[420px] text-left text-sm">
        <thead>
          <tr className="border-b border-[var(--border)] text-xs text-[var(--text-2)]">
            {columns.map((c) => <th key={c.header} className={`py-2 pr-4 font-normal ${c.align === 'right' ? 'text-right' : ''}`}>{c.header}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-[var(--border)]/60 last:border-0">
              {columns.map((c) => <td key={c.header} className={`mono py-2 pr-4 ${c.align === 'right' ? 'text-right' : ''}`}>{c.cell(r)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
