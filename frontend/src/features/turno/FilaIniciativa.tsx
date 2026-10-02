import {
  DndContext, KeyboardSensor, PointerSensor, closestCenter, useSensor, useSensors, type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext, arrayMove, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Flame, GripVertical, Plus, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { Icone, type Part } from './Participante'

function Item({ p, suaVez, travado, onRemover }: { p: Part; suaVez: boolean; travado: boolean; onRemover: () => void }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: p.id, disabled: travado })
  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={cn(
        'flex items-center gap-2 rounded-xl border bg-card p-2 text-sm',
        suaVez && 'border-primary ring-2 ring-primary/50',
        isDragging && 'z-10 opacity-80 shadow-lg',
      )}
    >
      <button {...attributes} {...listeners} disabled={travado}
        className="cursor-grab touch-none text-muted-foreground enabled:hover:text-foreground disabled:opacity-30" aria-label="Arrastar para reordenar">
        <GripVertical className="size-4" />
      </button>
      <span className="w-6 text-center font-semibold tabular-nums text-primary">{p.ordem}</span>
      <Icone p={p} className="size-8" />
      <span className="flex-1 truncate">{p.nome}</span>
      {suaVez && <Flame className="size-4 text-primary" />}
      <Button variant="ghost" size="icon-xs" disabled={travado} onClick={onRemover} aria-label="Tirar da fila"><X /></Button>
    </li>
  )
}

// Fila de iniciativa: arraste para reordenar. A posição na lista vira a ordem (1..n).
export function FilaIniciativa({
  participantes, emAndamento, ordemAtual, onSalvar,
}: {
  participantes: Part[]
  emAndamento: boolean
  ordemAtual: number | null
  onSalvar: (ids: string[]) => void
}) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )
  const fila = participantes.filter((p) => p.ordem).sort((a, b) => a.ordem! - b.ordem!)
  const semOrdem = participantes.filter((p) => !p.ordem)
  const ids = fila.map((p) => p.id)

  const aoSoltar = (e: DragEndEvent) => {
    if (!e.over || e.active.id === e.over.id) return
    onSalvar(arrayMove(ids, ids.indexOf(String(e.active.id)), ids.indexOf(String(e.over.id))))
  }

  return (
    <section className="space-y-3 rounded-2xl border bg-card p-4">
      <h2 className="font-semibold">⚔️ Ordem de iniciativa</h2>
      {fila.length === 0 && <p className="text-sm text-muted-foreground">Adicione participantes à fila abaixo.</p>}
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={aoSoltar}>
        <SortableContext items={ids} strategy={verticalListSortingStrategy}>
          <ol className="space-y-1.5">
            {fila.map((p) => (
              <Item key={p.id} p={p} travado={emAndamento} suaVez={emAndamento && p.ordem === ordemAtual}
                onRemover={() => onSalvar(ids.filter((i) => i !== p.id))} />
            ))}
          </ol>
        </SortableContext>
      </DndContext>
      {emAndamento && <p className="text-xs text-muted-foreground">A ordem fica travada durante o combate.</p>}
      {semOrdem.length > 0 && (
        <div className="space-y-1.5 border-t pt-3">
          <p className="text-xs text-muted-foreground">Sem ordem (clique para entrar no fim da fila)</p>
          <div className="flex flex-wrap gap-1.5">
            {semOrdem.map((p) => (
              <Button key={p.id} variant="outline" size="sm" onClick={() => onSalvar([...ids, p.id])}>
                <Plus /> {p.nome}
              </Button>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
