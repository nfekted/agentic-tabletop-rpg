import { useState } from 'react'
import {
  DndContext, DragOverlay, PointerSensor, closestCenter, useDraggable, useDroppable, useSensor, useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import { Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { TurnoArea } from '@/lib/types'
import { cn } from '@/lib/utils'
import { CardParticipante, type Part } from './Participante'

type Acoes = {
  ordemAtual: number | null
  emAndamento: boolean
  onFicha: (p: Part) => void
  onRemoverToken: (p: Part) => void
}

function Arrastavel({ p, acoes }: { p: Part; acoes: Acoes }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({ id: p.id })
  return (
    <div ref={setNodeRef} className={cn(isDragging && 'opacity-30')}>
      <CardParticipante
        p={p}
        suaVez={acoes.emAndamento && !!p.ordem && p.ordem === acoes.ordemAtual}
        handle={{ ...attributes, ...listeners }}
        onFicha={p.tipo === 'token' ? () => acoes.onFicha(p) : undefined}
        onRemover={p.tipo === 'token' ? () => acoes.onRemoverToken(p) : undefined}
      />
    </div>
  )
}

function Zona({
  id, titulo, itens, acoes, onExcluir, vazio,
}: { id: string; titulo: string; itens: Part[]; acoes: Acoes; onExcluir?: () => void; vazio: string }) {
  const { setNodeRef, isOver } = useDroppable({ id })
  return (
    <div ref={setNodeRef}
      className={cn('min-h-32 space-y-2 rounded-2xl border border-dashed bg-card/40 p-3 transition-colors', isOver && 'border-primary bg-primary/10')}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">{titulo}</h3>
        {onExcluir && <Button variant="ghost" size="icon-xs" onClick={onExcluir} aria-label="Excluir área" className="hover:text-destructive"><Trash2 /></Button>}
      </div>
      {itens.length === 0 && <p className="py-4 text-center text-xs text-muted-foreground">{vazio}</p>}
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
        {itens.map((p) => <Arrastavel key={p.id} p={p} acoes={acoes} />)}
      </div>
    </div>
  )
}

// Áreas da cena: arraste participantes entre as áreas (ou de volta para "Soltos").
export function Areas({
  areas, participantes, acoes, onCriar, onExcluir, onMover,
}: {
  areas: TurnoArea[]
  participantes: Part[]
  acoes: Acoes
  onCriar: (nome: string) => void
  onExcluir: (id: string) => void
  onMover: (participanteId: string, areaId: string | null) => void
}) {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }))
  const [nome, setNome] = useState('')
  const [arrastando, setArrastando] = useState<Part | null>(null)

  const emArea = new Set(areas.flatMap((a) => a.participantes))
  const soltos = participantes.filter((p) => !emArea.has(p.id))
  const porId = (ids: string[]) => ids.map((i) => participantes.find((p) => p.id === i)).filter((p): p is Part => !!p)

  const aoSoltar = (e: DragEndEvent) => {
    setArrastando(null)
    if (!e.over) return
    const id = String(e.active.id)
    const destino = String(e.over.id)
    const areaAtual = areas.find((a) => a.participantes.includes(id))?.id ?? null
    const novaArea = destino === 'soltos' ? null : destino.replace(/^area:/, '')
    if (areaAtual !== novaArea) onMover(id, novaArea)
  }

  const criar = () => { if (nome.trim()) { onCriar(nome.trim()); setNome('') } }

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold">🗺️ Áreas da cena</h2>
        <div className="flex gap-1.5">
          <Input value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Nova área (Entrada, Salão…)" className="w-56"
            onKeyDown={(e) => e.key === 'Enter' && criar()} />
          <Button variant="secondary" disabled={!nome.trim()} onClick={criar}><Plus /> Área</Button>
        </div>
      </div>
      <DndContext sensors={sensors} collisionDetection={closestCenter}
        onDragStart={(e) => setArrastando(participantes.find((p) => p.id === e.active.id) ?? null)}
        onDragEnd={aoSoltar} onDragCancel={() => setArrastando(null)}>
        <div className="grid gap-3 md:grid-cols-2 2xl:grid-cols-3">
          <Zona id="soltos" titulo="Soltos (sem área)" itens={soltos} acoes={acoes} vazio="Todos já estão em alguma área." />
          {areas.map((a) => (
            <Zona key={a.id} id={`area:${a.id}`} titulo={a.nome} itens={porId(a.participantes)} acoes={acoes}
              onExcluir={() => onExcluir(a.id)} vazio="Arraste participantes para cá." />
          ))}
        </div>
        <DragOverlay>
          {arrastando && <div className="w-64"><CardParticipante p={arrastando} suaVez={false} sobreposto /></div>}
        </DragOverlay>
      </DndContext>
    </section>
  )
}
