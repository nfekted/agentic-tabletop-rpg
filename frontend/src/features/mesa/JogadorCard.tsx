import { BookOpen, Camera, Eye, HeartPulse, Loader2, Pencil, Skull, Trash2 } from 'lucide-react'
import { Avatar } from '@/components/Avatar'
import { Balao } from '@/components/Balao'
import { ContextoBarra } from '@/components/ContextoBarra'
import { StatusBars } from '@/components/StatusBars'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { usePensando } from '@/hooks/eventos'
import { useAcao } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { Fala, Jogador } from '@/lib/types'
import { useUi } from '@/lib/ui-context'
import { cn } from '@/lib/utils'

function Acao({ icone: Icone, rotulo, onClick, perigo }: {
  icone: typeof Pencil; rotulo: string; onClick: () => void; perigo?: boolean
}) {
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onClick}
            aria-label={rotulo}
            className={perigo ? 'hover:text-destructive' : undefined}
          />
        }
      >
        <Icone />
      </TooltipTrigger>
      <TooltipContent>{rotulo}</TooltipContent>
    </Tooltip>
  )
}

export function JogadorCard({ jogador: j, fala }: { jogador: Jogador; fala?: Fala }) {
  const { abrir } = useUi()
  const pensando = usePensando().has(j.nome)
  const mods = j.modificadores.split(',').map((m) => m.trim()).filter(Boolean)
  const alternarMorto = useAcao(
    () => api.put(`/jogadores/${j.nome}/morto`, { morto: !j.morto }),
    [['jogadores'], ['sessao'], ['turno']],
    j.morto ? `${j.nome} voltou à mesa.` : `${j.nome} foi marcado como morto.`,
  )

  return (
    <article className={cn('flex flex-col gap-3 rounded-2xl border bg-card p-4 shadow-sm', j.morto && 'opacity-60')}>
      <Balao fala={fala} />
      <div className="flex items-center gap-3">
        <Avatar nome={j.nome} v={j.avatar_v} />
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-semibold">{j.nome}</h3>
          {j.morto ? (
            <p className="flex items-center gap-1 text-xs text-destructive"><Skull className="size-3" /> Morto</p>
          ) : pensando ? (
            <p className="flex items-center gap-1 text-xs text-primary">
              <Loader2 className="size-3 animate-spin" /> pensando…
            </p>
          ) : (
            <p className="text-xs text-muted-foreground">{mods.length ? '' : 'sem modificadores'}</p>
          )}
        </div>
      </div>
      {mods.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {mods.map((m) => <Badge key={m} variant="secondary">{m}</Badge>)}
        </div>
      )}
      {j.situacao && (
        <div className="flex flex-wrap gap-1">
          {j.situacao.split(', ').map((s) => <Badge key={s} variant="outline" className="border-destructive/50 text-destructive">{s}</Badge>)}
        </div>
      )}
      <StatusBars status={j.status} urlAjuste={`/fichas/${j.nome}/status/ajustar`} />
      {!j.morto && <ContextoBarra ctx={j.contexto} />}
      <div className="-mx-1 mt-auto flex items-center justify-between border-t pt-2">
        <div className="flex">
          <Acao icone={Pencil} rotulo="Editar ficha" onClick={() => abrir({ tipo: 'ficha-editar', nome: j.nome })} />
          <Acao icone={Eye} rotulo="Ver ficha" onClick={() => abrir({ tipo: 'ficha-ver', nome: j.nome })} />
          <Acao icone={BookOpen} rotulo="Memória" onClick={() => abrir({ tipo: 'memoria', nome: j.nome })} />
          <Acao icone={Camera} rotulo="Foto" onClick={() => abrir({ tipo: 'avatar', nome: j.nome })} />
        </div>
        <div className="flex">
          <Acao
            icone={j.morto ? HeartPulse : Skull}
            rotulo={j.morto ? 'Reviver (volta a receber mensagens)' : 'Marcar como morto'}
            perigo={!j.morto}
            onClick={() => alternarMorto.mutate()}
          />
          <Acao icone={Trash2} rotulo="Excluir jogador" perigo onClick={() => abrir({ tipo: 'excluir-jogador', nome: j.nome })} />
        </div>
      </div>
    </article>
  )
}
