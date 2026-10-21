import { useState } from 'react'
import { Eye, Flame, GripVertical, Pencil, ScrollText, Trash2 } from 'lucide-react'
import { Avatar } from '@/components/Avatar'
import { Balao } from '@/components/Balao'
import { ContextoBarra } from '@/components/ContextoBarra'
import { StatusBars } from '@/components/StatusBars'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { tokenImagemUrl } from '@/lib/api'
import type { Fala, Jogador, TurnoToken } from '@/lib/types'
import { useUi } from '@/lib/ui-context'
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
  const { abrir } = useUi()
  const status = p.tipo === 'personagem' ? (p.jogador?.status ?? []) : p.token.ficha_dados.status
  const situacao = (p.tipo === 'personagem' ? p.jogador?.situacao : p.token.situacao) ?? ''
  return (
    <div className={cn(
      'space-y-2 rounded-xl border bg-card p-2.5 text-sm shadow-sm',
      suaVez && 'border-primary ring-2 ring-primary/50',
      sobreposto && 'rotate-1 shadow-xl',
    )}>
      {p.tipo === 'personagem' && <Balao fala={p.fala} compacto />}
      <p className="flex items-start gap-1 break-words font-medium">
        {suaVez && <Flame className="mt-0.5 size-4 shrink-0 text-primary" />}{p.nome}
      </p>
      <div className="flex items-center gap-2">
        {handle && (
          <button {...handle} className="cursor-grab touch-none text-muted-foreground hover:text-foreground active:cursor-grabbing" aria-label="Arrastar">
            <GripVertical className="size-4" />
          </button>
        )}
        <Icone p={p} />
        <p className="min-w-0 flex-1 text-[11px] text-muted-foreground">{p.ordem ? `Iniciativa #${p.ordem}` : 'sem ordem'}</p>
        {p.tipo === 'personagem' && (
          <>
            <Button variant="ghost" size="icon-sm" onClick={() => abrir({ tipo: 'ficha-editar', nome: p.nome })} aria-label="Editar ficha" title="Editar ficha"><Pencil /></Button>
            <Button variant="ghost" size="icon-sm" onClick={() => abrir({ tipo: 'ficha-ver', nome: p.nome })} aria-label="Ver ficha" title="Ver ficha"><Eye /></Button>
          </>
        )}
        {onFicha && <Button variant="ghost" size="icon-sm" onClick={onFicha} aria-label="Ficha do token" title="Ficha do token"><ScrollText /></Button>}
        {onRemover && <Button variant="ghost" size="icon-sm" onClick={onRemover} aria-label="Remover do combate" title="Remover do combate" className="hover:text-destructive"><Trash2 /></Button>}
      </div>
      {situacao && (
        <div className="flex flex-wrap gap-1">
          {situacao.split(', ').map((s) => <Badge key={s} variant="outline" className="border-destructive/50 text-destructive">{s}</Badge>)}
        </div>
      )}
      <StatusBars status={status} compacto urlAjuste={p.tipo === 'personagem' ? `/fichas/${p.nome}/status/ajustar` : `/turno/tokens/${p.id}/status/ajustar`} />
      {p.tipo === 'personagem' && <ContextoBarra ctx={p.jogador?.contexto ?? null} compacto />}
    </div>
  )
}
