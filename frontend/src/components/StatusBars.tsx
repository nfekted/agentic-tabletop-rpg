import type { Status } from '@/lib/types'

export function StatusBars({ status, compacto }: { status: Status[]; compacto?: boolean }) {
  if (!status.length) return null
  return (
    <div className={compacto ? 'space-y-1' : 'space-y-1.5'}>
      {status.map((s) => {
        const pct = s.valor_max > 0 ? Math.max(0, Math.min(100, (s.valor_atual / s.valor_max) * 100)) : 0
        return (
          <div key={s.nome} title={`${s.nome}: ${s.valor_atual}/${s.valor_max}`}>
            <div className="flex justify-between text-[11px] leading-none text-muted-foreground">
              <span className="truncate">{s.nome}</span>
              <span className="tabular-nums">{s.valor_atual}/{s.valor_max}</span>
            </div>
            <div className="mt-0.5 h-1.5 overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: s.cor }} />
            </div>
          </div>
        )
      })}
    </div>
  )
}
