import { useState } from 'react'
import {
  DndContext, DragOverlay, PointerSensor, useDraggable, useDroppable, useSensor, useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import { ArrowLeftRight, Copy, GripVertical, Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { Item, Itens } from '@/lib/types'
import { cn } from '@/lib/utils'

type Zona = 'equipamento' | 'mochila'

const ZONAS: { id: Zona; titulo: string; adicionar: string; mover: string; vazio: string }[] = [
  { id: 'equipamento', titulo: 'Equipamento', adicionar: 'Equipamento', mover: 'Guardar na mochila', vazio: 'Nada equipado. Arraste um item da mochila para cá.' },
  { id: 'mochila', titulo: 'Mochila', adicionar: 'Item', mover: 'Equipar', vazio: 'Mochila vazia. Arraste um equipamento para cá.' },
]

const itemVazio = (): Item => ({
  nome: '', maos: null, peso: null, alcance: '', dano: '',
  porcentagem_crit: null, multiplicador_critico: null, descricao: '',
})
const numero = (v: string) => (v === '' ? null : Number(v))
const arredondar = (n: number) => Math.round(n * 100) / 100

function Campo({ rotulo, children, className }: { rotulo: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('space-y-0.5', className)}>
      <Label className="text-[11px] text-muted-foreground">{rotulo}</Label>
      {children}
    </div>
  )
}

function Cartao({
  item, zona, indice, destinoMover, onChange, onMover, onDuplicar, onRemover,
}: {
  item: Item; zona: Zona; indice: number; destinoMover: string
  onChange: (patch: Partial<Item>) => void
  onMover: () => void; onDuplicar: () => void; onRemover: () => void
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({ id: `${zona}:${indice}` })
  return (
    <div ref={setNodeRef} className={cn('space-y-2 rounded-xl border bg-card p-2.5', isDragging && 'opacity-30')}>
      <div className="flex items-center gap-1.5">
        <button {...attributes} {...listeners} className="cursor-grab touch-none text-muted-foreground hover:text-foreground active:cursor-grabbing" aria-label="Arrastar item">
          <GripVertical className="size-4" />
        </button>
        <Input value={item.nome} placeholder="Nome do item (obrigatório)" aria-label="Nome do item" aria-invalid={!item.nome.trim()}
          onChange={(e) => onChange({ nome: e.target.value })} className="flex-1" />
        <Button variant="ghost" size="icon-sm" onClick={onMover} aria-label={destinoMover} title={destinoMover}><ArrowLeftRight /></Button>
        <Button variant="ghost" size="icon-sm" onClick={onDuplicar} aria-label="Duplicar item" title="Duplicar item"><Copy /></Button>
        <Button variant="ghost" size="icon-sm" onClick={onRemover} aria-label="Remover item" className="hover:text-destructive"><Trash2 /></Button>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        <Campo rotulo="Mãos"><Input type="number" min={0} step={1} value={item.maos ?? ''} onChange={(e) => onChange({ maos: numero(e.target.value) })} /></Campo>
        <Campo rotulo="Peso"><Input type="number" min={0} step="any" value={item.peso ?? ''} onChange={(e) => onChange({ peso: numero(e.target.value) })} /></Campo>
        <Campo rotulo="Alcance"><Input value={item.alcance} placeholder="Curto" onChange={(e) => onChange({ alcance: e.target.value })} /></Campo>
        <Campo rotulo="Dano"><Input value={item.dano} placeholder="1~4" onChange={(e) => onChange({ dano: e.target.value })} /></Campo>
        <Campo rotulo="% crítico"><Input type="number" min={0} step={1} value={item.porcentagem_crit ?? ''} onChange={(e) => onChange({ porcentagem_crit: numero(e.target.value) })} /></Campo>
        <Campo rotulo="Mult. crítico"><Input type="number" min={0} step="any" value={item.multiplicador_critico ?? ''} onChange={(e) => onChange({ multiplicador_critico: numero(e.target.value) })} /></Campo>
        <Campo rotulo="Descrição" className="col-span-2 sm:col-span-3">
          <Input value={item.descricao} placeholder="pequena adaga" onChange={(e) => onChange({ descricao: e.target.value })} />
        </Campo>
      </div>
    </div>
  )
}

function Painel({ id, titulo, vazio, rodape, children }: {
  id: Zona; titulo: string; vazio: string; rodape: React.ReactNode; children: React.ReactNode[]
}) {
  const { setNodeRef, isOver } = useDroppable({ id })
  return (
    <section ref={setNodeRef}
      className={cn('flex min-h-40 flex-col gap-2 rounded-xl border border-dashed p-3 transition-colors', isOver && 'border-primary bg-primary/10')}>
      <h3 className="text-sm font-semibold">{titulo}</h3>
      {children.length === 0 && <p className="py-3 text-center text-xs text-muted-foreground">{vazio}</p>}
      {children}
      <div className="mt-auto flex justify-end">{rodape}</div>
    </section>
  )
}

// Equipamento e Mochila: arraste os itens entre os painéis (ou use o botão de mover).
export function ItensEditor({ valor, onChange }: { valor: Itens; onChange: (i: Itens) => void }) {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }))
  const [arrastando, setArrastando] = useState<Item | null>(null)

  const setLista = (z: Zona, l: Item[]) => onChange({ ...valor, [z]: l })
  const mover = (de: Zona, i: number) => {
    const para: Zona = de === 'equipamento' ? 'mochila' : 'equipamento'
    onChange({ ...valor, [de]: valor[de].filter((_, k) => k !== i), [para]: [...valor[para], valor[de][i]] })
  }
  const aoSoltar = (e: DragEndEvent) => {
    setArrastando(null)
    if (!e.over) return
    const [de, idx] = String(e.active.id).split(':')
    const para = String(e.over.id)
    if ((para === 'equipamento' || para === 'mochila') && para !== de) mover(de as Zona, Number(idx))
  }

  const carregado = arredondar([...valor.equipamento, ...valor.mochila].reduce((s, i) => s + (i.peso ?? 0), 0))
  const livre = arredondar(valor.tamanho_mochila - carregado)
  const semNome = [...valor.equipamento, ...valor.mochila].some((i) => !i.nome.trim())

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-end gap-4 rounded-xl border p-3">
        <Campo rotulo="Tamanho da mochila">
          <Input type="number" min={0} step={1} className="w-28" value={valor.tamanho_mochila}
            onChange={(e) => onChange({ ...valor, tamanho_mochila: Math.max(0, Math.trunc(Number(e.target.value) || 0)) })} />
        </Campo>
        <p className={cn('pb-1.5 text-sm', livre < 0 ? 'font-medium text-destructive' : 'text-muted-foreground')}>
          Peso carregado: {carregado} · <b>{livre}</b> de {valor.tamanho_mochila} livres{livre < 0 && ' (sobrecarregado)'}
        </p>
      </div>

      <DndContext sensors={sensors} onDragStart={(e) => {
        const [z, i] = String(e.active.id).split(':')
        setArrastando(valor[z as Zona][Number(i)] ?? null)
      }} onDragEnd={aoSoltar} onDragCancel={() => setArrastando(null)}>
        <div className="grid gap-3 md:grid-cols-2">
          {ZONAS.map((z) => (
            <Painel key={z.id} id={z.id} titulo={z.titulo} vazio={z.vazio}
              rodape={
                <Button variant="outline" size="sm" onClick={() => setLista(z.id, [...valor[z.id], itemVazio()])}>
                  <Plus /> {z.adicionar}
                </Button>
              }>
              {valor[z.id].map((item, i) => (
                <Cartao key={i} item={item} zona={z.id} indice={i} destinoMover={z.mover}
                  onChange={(patch) => setLista(z.id, valor[z.id].map((x, k) => (k === i ? { ...x, ...patch } : x)))}
                  onMover={() => mover(z.id, i)}
                  onDuplicar={() => setLista(z.id, [...valor[z.id].slice(0, i + 1), { ...item }, ...valor[z.id].slice(i + 1)])}
                  onRemover={() => setLista(z.id, valor[z.id].filter((_, k) => k !== i))} />
              ))}
            </Painel>
          ))}
        </div>
        <DragOverlay>
          {arrastando && <div className="rounded-xl border bg-card p-3 text-sm shadow-xl">{arrastando.nome || 'Item sem nome'}</div>}
        </DragOverlay>
      </DndContext>
      <p className="text-xs text-muted-foreground">
        {semNome ? 'Itens sem nome não são salvos. ' : ''}
        Na mochila, itens 100% iguais são agrupados no prompt (ex.: “2x Flecha”) — use <b>duplicar</b> para repetir um item.
      </p>
    </div>
  )
}
