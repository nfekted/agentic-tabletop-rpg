import { useEffect, useState } from 'react'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useLimites } from '@/hooks/queries'
import type { Limite } from '@/lib/types'

const ROTULOS = {
  rpm: 'Requisições por minuto',
  tpm: 'Tokens por minuto',
  rpd: 'Requisições por dia',
} as const

const fmtTempo = (s: number) => {
  if (s >= 3600) return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}min`
  return s >= 60 ? `${Math.floor(s / 60)}min ${s % 60}s` : `${s}s`
}
const fmtNum = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(1).replace('.0', '')}k` : String(n))
const cor = (pct: number) => (pct >= 90 ? '#e74c3c' : pct >= 70 ? '#f39c12' : '#2ecc71')

function Anel({ sigla, l, decorrido }: { sigla: keyof typeof ROTULOS; l: Limite; decorrido: number }) {
  const zera = Math.max(0, l.zera_em - decorrido)
  const libera = Math.max(0, l.libera_em - decorrido)
  const expirou = sigla !== 'rpd' && l.usado > 0 && zera === 0
  const usado = expirou ? 0 : l.usado
  const pct = Math.min(100, (usado / l.limite) * 100)
  const r = 15
  const c = 2 * Math.PI * r
  return (
    <Tooltip>
      <TooltipTrigger render={<div className="flex w-12 shrink-0 cursor-help flex-col items-center" />}>
        <div className="relative size-9">
          <svg viewBox="0 0 36 36" className="size-9 -rotate-90">
            <circle cx="18" cy="18" r={r} fill="none" strokeWidth="3" className="stroke-muted" />
            <circle cx="18" cy="18" r={r} fill="none" strokeWidth="3" strokeLinecap="round"
              strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)}
              style={{ stroke: cor(pct), transition: 'stroke-dashoffset .4s, stroke .4s' }} />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-[10px] font-medium tabular-nums">
            {fmtNum(usado)}
          </span>
        </div>
        <span className="text-[9px] leading-tight text-muted-foreground uppercase">{sigla}</span>
      </TooltipTrigger>
      <TooltipContent side="right" className="space-y-0.5 text-xs">
        <p className="font-medium">{sigla.toUpperCase()}: {usado.toLocaleString('pt-BR')} / {l.limite.toLocaleString('pt-BR')}</p>
        <p className="opacity-70">{ROTULOS[sigla]}</p>
        {usado > 0 ? (
          <>
            <p>Zera em {fmtTempo(zera)}</p>
            {sigla !== 'rpd' && libera < zera && <p>Libera espaço em {fmtTempo(libera)}</p>}
          </>
        ) : (
          <p>Sem uso na janela atual</p>
        )}
      </TooltipContent>
    </Tooltip>
  )
}

// Anéis de uso dos limites de RPM/TPM/RPD da LLM; só aparecem os que têm limite configurado.
export function LimitesSidebar() {
  const { data, dataUpdatedAt } = useLimites()
  const [agora, setAgora] = useState(() => Date.now())
  useEffect(() => {
    const t = setInterval(() => setAgora(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])
  if (!data) return null
  const decorrido = Math.max(0, Math.floor((agora - dataUpdatedAt) / 1000))
  const ativos = (['rpm', 'tpm', 'rpd'] as const).filter((k) => data[k].limite > 0)
  if (ativos.length === 0) return null
  return (
    <div className="hidden flex-col items-center gap-1.5 pb-1 md:flex">
      {ativos.map((k) => <Anel key={k} sigla={k} l={data[k]} decorrido={decorrido} />)}
    </div>
  )
}
