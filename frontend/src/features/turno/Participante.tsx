import { useState } from 'react'
import { Flame, GripVertical, ScrollText, Trash2 } from 'lucide-react'
import { Avatar } from '@/components/Avatar'
import { Balao } from '@/components/Balao'
import { ContextoBarra } from '@/components/ContextoBarra'
import { StatusBars } from '@/components/StatusBars'
import { Button } from '@/components/ui/button'
import { tokenImagemUrl } from '@/lib/api'
import type { Fala, Jogador, TurnoToken } from '@/lib/types'
import { cn } from '@/lib/utils'

// Participante do combate: personagem (jogador) ou token (cópia isolada de inimigo/NPC/item).
export type Part =
  | { id: string; tipo: 'personagem'; nome: string; ordem: number | null; jogador?: Jogador; fala?: Fala }
  | { id: string; tipo: 'token'; nome: string; ordem: number | null; token: TurnoToken; imagem?: boolean }

export function Icone({ p, className }: { p: Part; className?: string }) {
  const [erro, setErro] = useState(false)
  if (p.tipo === 'personagem') return <Avatar nome={p.nome} v={p.jogador?.avatar_v ?? null} className={cn('size-9', className)} />
  if (p.token.arquivo && p.imagem && !erro)
    return <img src={tokenImagemUrl(p.token.categoria, p.token.arquivo)} onError={() => setErro(true)} alt=""
      className={cn('size-9 shrink-0 rounded-xl object-cover ring-1 ring-border', className)} />
  return <div className={cn('flex size-9 shrink-0 items-center justify-center rounded-xl bg-muted text-lg', className)}>{p.token.tipo_icone}</div>
}

export function CardParticipante({
  p, suaVez, handle, onFicha, onRemover, sobreposto,
}: {
  p: Part
  suaVez: boolean
  handle?: React.HTMLAttributes<HTMLElement>
  onFicha?: () => void
  onRemover?: () => void
  sobreposto?: boolean
}) {
  const status = p.tipo === 'personagem' ? (p.jogador?.status ?? []) : p.token.ficha_dados.status
  return (
    <div className={cn(
      'space-y-2 rounded-xl border bg-card p-2.5 text-sm shadow-sm',
      suaVez && 'border-primary ring-2 ring-primary/50',
      sobreposto && 'rotate-1 shadow-xl',
    )}>
      {p.tipo === 'personagem' && <Balao fala={p.fala} compacto />}
      <div className="flex items-center gap-2">
        {handle && (
          <button {...handle} className="cursor-grab touch-none text-muted-foreground hover:text-foreground active:cursor-grabbing" aria-label="Arrastar">
            <GripVertical className="size-4" />
          </button>
        )}
        <Icone p={p} />
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-1 truncate font-medium">
            {suaVez && <Flame className="size-4 shrink-0 text-primary" />}{p.nome}
          </p>
          <p className="text-[11px] text-muted-foreground">{p.ordem ? `Iniciativa #${p.ordem}` : 'sem ordem'}</p>
        </div>
        {onFicha && <Button variant="ghost" size="icon-sm" onClick={onFicha} aria-label="Ficha do token"><ScrollText /></Button>}
        {onRemover && <Button variant="ghost" size="icon-sm" onClick={onRemover} aria-label="Remover do combate" className="hover:text-destructive"><Trash2 /></Button>}
      </div>
      <StatusBars status={status} compacto urlAjuste={p.tipo === 'personagem' ? `/fichas/${p.nome}/status/ajustar` : `/turno/tokens/${p.id}/status/ajustar`} />
      {p.tipo === 'personagem' && <ContextoBarra ctx={p.jogador?.contexto ?? null} compacto />}
    </div>
  )
}
