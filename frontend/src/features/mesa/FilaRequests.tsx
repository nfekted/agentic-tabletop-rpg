import { useEffect, useState } from 'react'
import { AlertTriangle, Binary, Check, Dices, Loader2, Play, X } from 'lucide-react'
import { Avatar } from '@/components/Avatar'
import { Button } from '@/components/ui/button'
import { filaOcupada, useAcao, useFila, useJogadores } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { Fila, FilaItem } from '@/lib/types'
import { cn } from '@/lib/utils'

type Estado = 'pendente' | 'ativo' | 'ok' | 'erro'

const ETAPAS = { rodada: 'da rodada', cena: 'da cena', mesa: 'da mesa' } as const
const fmtTempo = (s: number) => (s >= 60 ? `${Math.floor(s / 60)}min ${s % 60}s` : `${s}s`)

function Linha({ ok }: { ok: boolean }) {
  return <div className={cn('mt-6 h-px w-6 shrink-0 self-start sm:w-10', ok ? 'bg-emerald-500' : 'bg-border')} />
}

function No({ estado, rotulo, children }: { estado: Estado; rotulo: string; children: React.ReactNode }) {
  return (
    <div className="flex w-20 shrink-0 flex-col items-center gap-1 text-center">
      <div
        className={cn(
          'relative flex size-12 items-center justify-center rounded-xl text-muted-foreground ring-2 transition-colors',
          estado === 'pendente' && 'opacity-50 ring-border',
          estado === 'ativo' && 'text-primary ring-primary',
          estado === 'ok' && 'text-emerald-500 ring-emerald-500',
          estado === 'erro' && 'text-destructive ring-destructive',
        )}
      >
        {children}
      </div>
      <span className={cn('line-clamp-2 text-[11px] leading-tight', estado === 'ativo' ? 'font-medium' : 'text-muted-foreground')}>
        {rotulo}
      </span>
    </div>
  )
}

function estadosDoItem(it: FilaItem): { avatar: Estado; verificando: Estado; interpretando: Estado } {
  switch (it.status) {
    case 'ok': return { avatar: 'ok', verificando: 'ok', interpretando: 'ok' }
    case 'verificando':
    case 'aguardando': return { avatar: 'ativo', verificando: 'ativo', interpretando: 'pendente' }
    case 'interpretando': return { avatar: 'ativo', verificando: 'ok', interpretando: 'ativo' }
    case 'erro': return { avatar: 'erro', verificando: it.tokens_previstos ? 'ok' : 'erro', interpretando: it.tokens_previstos ? 'erro' : 'pendente' }
    default: return { avatar: 'pendente', verificando: 'pendente', interpretando: 'pendente' }
  }
}

function Passos({ fila }: { fila: Fila }) {
  const { data: jogadores = [] } = useJogadores()
  return (
    <div className="flex items-start overflow-x-auto pb-1">
      {fila.itens.map((it, i) => {
        const e = estadosDoItem(it)
        const jogador = jogadores.find((j) => j.nome === it.agente)
        const esperando = it.status === 'aguardando'
        return (
          <div key={`${it.agente}-${i}`} className="flex items-start">
            {i > 0 && <Linha ok={fila.itens[i - 1].status === 'ok'} />}
            <No estado={e.avatar} rotulo={it.agente}>
              <Avatar nome={it.agente} v={jogador?.avatar_v ?? null} className="size-full rounded-[10px] ring-0" />
              {e.avatar === 'ok' && (
                <span className="absolute -right-1.5 -top-1.5 flex size-4 items-center justify-center rounded-full bg-emerald-500 text-white">
                  <Check className="size-3" />
                </span>
              )}
            </No>
            <Linha ok={e.verificando === 'ok'} />
            <No estado={e.verificando} rotulo={esperando ? 'Aguardando limite' : 'Verificando contexto'}>
              {esperando ? <Loader2 className="size-5 animate-spin" /> : <Binary className="size-5" />}
            </No>
            <Linha ok={e.interpretando === 'ok'} />
            <No estado={e.interpretando} rotulo={it.etapa ? `Interpretando ${ETAPAS[it.etapa]}` : 'Interpretando'}>
              <Dices className={cn('size-5', e.interpretando === 'ativo' && 'animate-pulse')} />
            </No>
          </div>
        )
      })}
    </div>
  )
}

export function FilaRequests() {
  const { data: fila, dataUpdatedAt } = useFila()
  const [agora, setAgora] = useState(() => Date.now())
  const continuar = useAcao(() => api.post('/fila/continuar'), [['fila']])
  const cancelar = useAcao(() => api.post('/fila/cancelar'), [['fila']])

  const esperando = fila?.status === 'aguardando_limite'
  useEffect(() => {
    if (!esperando) return
    const t = setInterval(() => setAgora(Date.now()), 1000)
    return () => clearInterval(t)
  }, [esperando])

  if (!fila || !filaOcupada(fila)) return null

  const pausada = fila.status === 'pausada'
  const atual = fila.itens[Math.min(fila.indice, fila.itens.length - 1)]
  const decorrido = Math.max(0, Math.floor((agora - dataUpdatedAt) / 1000))
  const restante = fila.espera_ate ? Math.max(0, Math.ceil(fila.espera_ate - fila.agora) - decorrido) : 0
  const ocupado = continuar.isPending || cancelar.isPending

  return (
    <section className={cn('space-y-3 rounded-2xl border bg-card p-4', pausada && 'border-destructive/60')}>
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="font-semibold">📥 Fila de requests</h2>
        <span className="text-xs text-muted-foreground">
          {fila.itens.filter((i) => i.status === 'ok').length}/{fila.itens.length}
          {!pausada && atual && ` · ${atual.agente}`}
          {!pausada && atual?.tokens_previstos ? ` · ~${atual.tokens_previstos.toLocaleString('pt-BR')} tokens previstos` : ''}
        </span>
        {!pausada && <Loader2 className="size-3.5 animate-spin text-primary" />}
        {!pausada && (
          <Button className="ml-auto" size="xs" variant="ghost" disabled={ocupado} onClick={() => cancelar.mutate()}>
            <X /> Cancelar fila
          </Button>
        )}
      </div>

      {fila.limites_ativos && <Passos fila={fila} />}

      {esperando && (
        <p className="text-sm text-amber-500">
          {fila.aviso ?? 'Aguardando o limite liberar.'} {restante > 0 && <b>Retoma em {fmtTempo(restante)}.</b>}
        </p>
      )}

      {pausada && (
        <div className="space-y-2 rounded-xl border border-destructive/40 bg-destructive/5 p-3">
          <p className="flex items-start gap-2 text-sm text-destructive">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />
            <span>
              A fila parou em <b>{atual?.agente}</b>: {fila.erro}
            </span>
          </p>
          <div className="flex gap-2">
            <Button size="sm" disabled={ocupado} onClick={() => continuar.mutate()}>
              {continuar.isPending ? <Loader2 className="animate-spin" /> : <Play />} Continuar de {atual?.agente}
            </Button>
            <Button size="sm" variant="outline" disabled={ocupado} onClick={() => cancelar.mutate()}>
              <X /> Cancelar fila
            </Button>
          </div>
        </div>
      )}
    </section>
  )
}
