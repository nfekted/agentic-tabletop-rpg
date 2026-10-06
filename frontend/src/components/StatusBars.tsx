import { Minus, Plus } from 'lucide-react'
import { useAcao } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { Status } from '@/lib/types'

// Com `urlAjuste`, mostra − e + nas pontas da barra para ajustar o valor atual de 1 em 1 (entre 0 e o máximo).
export function StatusBars({ status, compacto, urlAjuste }: { status: Status[]; compacto?: boolean; urlAjuste?: string }) {
  const ajustar = useAcao(
    (v: { nome: string; delta: number }) => api.post(`${urlAjuste}`, v),
    [['jogadores'], ['ficha'], ['turno']],
  )
  if (!status.length) return null
  const botao = 'flex size-4 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-30 disabled:hover:bg-transparent'
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
            <div className="mt-0.5 flex items-center gap-1">
              {urlAjuste && (
                <button className={botao} aria-label={`Diminuir ${s.nome}`} disabled={s.valor_atual <= 0 || ajustar.isPending}
                  onClick={() => ajustar.mutate({ nome: s.nome, delta: -1 })}><Minus className="size-3" /></button>
              )}
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: s.cor }} />
              </div>
              {urlAjuste && (
                <button className={botao} aria-label={`Aumentar ${s.nome}`} disabled={s.valor_atual >= s.valor_max || ajustar.isPending}
                  onClick={() => ajustar.mutate({ nome: s.nome, delta: 1 })}><Plus className="size-3" /></button>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
