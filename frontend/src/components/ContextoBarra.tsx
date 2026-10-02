import { Brain } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { Contexto } from '@/lib/types'

const CORES = { verde: '#2ecc71', ambar: '#f39c12', vermelho: '#e74c3c' }
const NOMES: Record<string, string> = {
  memoria: 'memória', ficha: 'ficha', regras: 'regras', base: 'prompt base', turno: 'histórico+instrução',
}
const fmt = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(1).replace('.0', '')}k` : String(n))

// Barra "🧠 Contexto": quanto do limite da LLM o último prompt ocupou. Some se o controle estiver desligado.
export function ContextoBarra({ ctx, compacto }: { ctx: Contexto | null; compacto?: boolean }) {
  if (!ctx) return null
  const cor = CORES[ctx.faixa]
  const pct = Math.max(0, Math.min(100, ctx.pct))
  return (
    <Tooltip>
      <TooltipTrigger
        render={<div className="block w-full cursor-help text-left" />}
      >
        <div className="flex items-center justify-between text-[11px] leading-none" style={{ color: cor }}>
          <span className="flex items-center gap-1 font-medium"><Brain className="size-3" />{!compacto && 'Contexto'}</span>
          <span className="tabular-nums">{ctx.pct.toFixed(0)}%</span>
        </div>
        <div className="relative mt-0.5 h-1.5 overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: cor }} />
          <span className="absolute top-0 h-full w-0.5 bg-black/60" style={{ left: `${ctx.gatilho_pct}%` }} />
        </div>
      </TooltipTrigger>
      <TooltipContent className="max-w-64 space-y-0.5 text-xs">
        <p>Contexto: {ctx.usado.toLocaleString('pt-BR')} / {ctx.limite.toLocaleString('pt-BR')} tokens ({ctx.pct}%)</p>
        <p>Gatilho de compressão: {ctx.gatilho_pct}%</p>
        <p>{Object.entries(ctx.partes).map(([k, v]) => `${NOMES[k] ?? k} ${fmt(v)}`).join(' · ')}</p>
        {ctx.estimado && <p className="opacity-70">valor estimado (sem medição exata do provedor)</p>}
      </TooltipContent>
    </Tooltip>
  )
}
