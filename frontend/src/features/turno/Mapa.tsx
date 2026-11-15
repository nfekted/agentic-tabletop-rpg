import { useRef, useState } from 'react'
import {
  DndContext, DragOverlay, PointerSensor, pointerWithin, useDraggable, useDroppable, useSensor, useSensors,
  type DragEndEvent, type DragMoveEvent,
} from '@dnd-kit/core'
import { Map as MapaIcone, PencilRuler, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { Pos, TurnoArea, TurnoMapa, TurnoObstaculo } from '@/lib/types'
import { cn } from '@/lib/utils'
import { CardParticipante, Icone, type Part } from './Participante'

const CELULA = 48 // px
const CORES_AREA = [
  'border-sky-400/70 bg-sky-400/10 text-sky-300',
  'border-emerald-400/70 bg-emerald-400/10 text-emerald-300',
  'border-amber-400/70 bg-amber-400/10 text-amber-300',
  'border-rose-400/70 bg-rose-400/10 text-rose-300',
  'border-violet-400/70 bg-violet-400/10 text-violet-300',
  'border-teal-400/70 bg-teal-400/10 text-teal-300',
]

type Ret = { x: number; y: number; largura: number; altura: number }
type Ferramenta = 'area' | 'obstaculo'

type Acoes = {
  ordemAtual: number | null
  emAndamento: boolean
  onFicha: (p: Part) => void
  onRemoverToken: (p: Part) => void
}

const retangulo = (a: Pos, b: Pos): Ret => ({
  x: Math.min(a.x, b.x), y: Math.min(a.y, b.y),
  largura: Math.abs(a.x - b.x) + 1, altura: Math.abs(a.y - b.y) + 1,
})
const sobrepoe = <T extends Ret>(r: Ret, lista: T[]) =>
  lista.find((a) => r.x < a.x + a.largura && a.x < r.x + r.largura && r.y < a.y + a.altura && a.y < r.y + r.altura)
const dentro = (r: Ret, c: Pos) => r.x <= c.x && c.x < r.x + r.largura && r.y <= c.y && c.y < r.y + r.altura
const pxRet = (r: Ret): React.CSSProperties =>
  ({ left: r.x * CELULA, top: r.y * CELULA, width: r.largura * CELULA, height: r.altura * CELULA })

function CriarMapa({ onCriar }: { onCriar: (largura: number, altura: number) => void }) {
  const [largura, setLargura] = useState('20')
  const [altura, setAltura] = useState('12')
  const l = Number(largura), a = Number(altura)
  const valido = Number.isInteger(l) && Number.isInteger(a) && l >= 1 && l <= 100 && a >= 1 && a <= 100
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed p-8 text-center">
      <MapaIcone className="size-8 text-muted-foreground" />
      <p className="text-sm text-muted-foreground">Ainda não há mapa. Escolha o tamanho em células (1 a 100); para mudar depois, exclua e crie outro.</p>
      <div className="flex items-center gap-1.5">
        <Input type="number" min={1} max={100} value={largura} onChange={(e) => setLargura(e.target.value)} className="w-20" aria-label="Largura" />
        <span className="text-muted-foreground">×</span>
        <Input type="number" min={1} max={100} value={altura} onChange={(e) => setAltura(e.target.value)} className="w-20" aria-label="Altura" />
        <Button disabled={!valido} onClick={() => onCriar(l, a)}>Criar mapa</Button>
      </div>
    </div>
  )
}

function Arrastavel({ p, desativado, className, style, onClick, children }: {
  p: Part; desativado?: boolean; className?: string; style?: React.CSSProperties; onClick: () => void; children: React.ReactNode
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({ id: p.id, disabled: desativado })
  return (
    <button ref={setNodeRef} {...attributes} {...listeners} onClick={onClick} title={p.nome} style={style}
      className={cn('touch-none', !desativado && 'cursor-grab active:cursor-grabbing', className, isDragging && 'opacity-30')}>
      {children}
    </button>
  )
}

// Camada do modo de edição: clique e arraste para desenhar o retângulo de uma área ou obstáculo.
function DesenharRet({ mapa, motivo, onConcluir }: { mapa: TurnoMapa; motivo: (r: Ret) => string | null; onConcluir: (r: Ret) => void }) {
  const [ini, setIni] = useState<Pos | null>(null)
  const [fim, setFim] = useState<Pos | null>(null)
  const cel = (e: React.PointerEvent<HTMLDivElement>): Pos => {
    const r = e.currentTarget.getBoundingClientRect()
    return {
      x: Math.max(0, Math.min(mapa.largura - 1, Math.floor((e.clientX - r.left) / CELULA))),
      y: Math.max(0, Math.min(mapa.altura - 1, Math.floor((e.clientY - r.top) / CELULA))),
    }
  }
  const ret = ini && fim ? retangulo(ini, fim) : null
  return (
    <div className="absolute inset-0 z-30 cursor-crosshair touch-none"
      onPointerDown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); const c = cel(e); setIni(c); setFim(c) }}
      onPointerMove={(e) => { if (ini) setFim(cel(e)) }}
      onPointerUp={() => { if (ret) onConcluir(ret); setIni(null); setFim(null) }}>
      {ret && <RetPrevia r={ret} invalido={!!motivo(ret)} />}
    </div>
  )
}

function RetPrevia({ r, invalido }: { r: Ret; invalido: boolean }) {
  return (
    <div className={cn('pointer-events-none absolute z-30 rounded-lg border-2 border-dashed',
      invalido ? 'border-destructive bg-destructive/20' : 'border-primary bg-primary/20')} style={pxRet(r)} />
  )
}

function Grade({ mapa, areas, obstaculos, grade, alvo, alvoLivre, editando, pendente, motivo, onDesenhar, onExcluirArea, onExcluirObstaculo, children }: {
  mapa: TurnoMapa; areas: TurnoArea[]; obstaculos: TurnoObstaculo[]; grade: React.RefObject<HTMLDivElement | null>
  alvo: Pos | null; alvoLivre: boolean
  editando: boolean; pendente: Ret | null; motivo: (r: Ret) => string | null; onDesenhar: (r: Ret) => void
  onExcluirArea: (id: string) => void; onExcluirObstaculo: (id: string) => void
  children: React.ReactNode
}) {
  const { setNodeRef } = useDroppable({ id: 'mapa' })
  return (
    <div ref={setNodeRef} className={cn('max-h-[70vh] overflow-auto rounded-2xl border bg-card/40 p-2', editando && 'border-primary')}>
      <div
        ref={grade}
        className="relative grid text-muted-foreground/15"
        style={{
          gridTemplateColumns: `repeat(${mapa.largura}, ${CELULA}px)`,
          gridTemplateRows: `repeat(${mapa.altura}, ${CELULA}px)`,
          width: mapa.largura * CELULA,
          backgroundImage: 'linear-gradient(to right, currentColor 1px, transparent 1px), linear-gradient(to bottom, currentColor 1px, transparent 1px)',
          backgroundSize: `${CELULA}px ${CELULA}px`,
          boxShadow: 'inset -1px -1px 0 currentColor',
        }}
      >
        {areas.map((a, i) => (
          <div key={a.id}
            className={cn('pointer-events-none flex items-start justify-between gap-1 rounded-lg border-2 p-1 text-[11px] font-semibold leading-none', CORES_AREA[i % CORES_AREA.length])}
            style={{ gridColumn: `${a.x + 1} / span ${a.largura}`, gridRow: `${a.y + 1} / span ${a.altura}` }}>
            <span className="truncate">{a.nome}</span>
            {editando && (
              <button onClick={() => onExcluirArea(a.id)} aria-label={`Excluir área ${a.nome}`} title={`Excluir área ${a.nome}`}
                className="pointer-events-auto relative z-40 rounded bg-card/80 p-0.5 text-muted-foreground hover:text-destructive">
                <Trash2 className="size-3.5" />
              </button>
            )}
          </div>
        ))}
        {obstaculos.map((o) => (
          <div key={o.id} title={o.nome || 'Obstáculo'}
            className="pointer-events-none flex items-start justify-between gap-1 overflow-hidden rounded-md border border-muted-foreground/50 p-0.5 text-[10px] leading-none text-muted-foreground"
            style={{
              gridColumn: `${o.x + 1} / span ${o.largura}`, gridRow: `${o.y + 1} / span ${o.altura}`,
              backgroundImage: 'repeating-linear-gradient(45deg, color-mix(in oklab, currentColor 35%, transparent) 0 2px, transparent 2px 8px)',
            }}>
            <span className="truncate rounded bg-card/80 px-0.5">{o.nome}</span>
            {editando && (
              <button onClick={() => onExcluirObstaculo(o.id)} aria-label={`Excluir obstáculo ${o.nome}`} title="Excluir obstáculo"
                className="pointer-events-auto relative z-40 shrink-0 rounded bg-card/80 p-0.5 hover:text-destructive">
                <Trash2 className="size-3" />
              </button>
            )}
          </div>
        ))}
        {alvo && (
          <div className={cn('pointer-events-none z-20 rounded-md border-2 border-dashed',
            alvoLivre ? 'border-primary bg-primary/20' : 'border-destructive bg-destructive/20')}
            style={{ gridColumn: alvo.x + 1, gridRow: alvo.y + 1 }} />
        )}
        {children}
        {pendente && <RetPrevia r={pendente} invalido={!!motivo(pendente)} />}
        {editando && !pendente && <DesenharRet mapa={mapa} motivo={motivo} onConcluir={onDesenhar} />}
      </div>
    </div>
  )
}

function ForaDoMapa({ vazio, children }: { vazio: boolean; children: React.ReactNode }) {
  const { setNodeRef, isOver } = useDroppable({ id: 'fora' })
  return (
    <div ref={setNodeRef} className={cn('rounded-2xl border border-dashed bg-card/40 p-3 transition-colors', isOver && 'border-primary bg-primary/10')}>
      <h3 className="mb-2 text-sm font-semibold">Fora do mapa</h3>
      {vazio
        ? <p className="text-xs text-muted-foreground">Todos estão no mapa. Arraste alguém para cá para tirá-lo.</p>
        : <div className="flex flex-wrap gap-1.5">{children}</div>}
    </div>
  )
}

function NomearRet({ r, ferramenta, problema, onCriar, onCancelar }: {
  r: Ret; ferramenta: Ferramenta; problema: string | null; onCriar: (nome: string) => void; onCancelar: () => void
}) {
  const [nome, setNome] = useState('')
  const area = ferramenta === 'area'
  const ok = (!area || !!nome.trim()) && !problema
  return (
    <div className="flex flex-wrap items-center gap-1.5 rounded-xl border bg-card p-2 text-sm">
      <span className="text-muted-foreground">{area ? 'Nova área' : 'Novo obstáculo'} {r.largura} × {r.altura}:</span>
      <Input autoFocus value={nome} onChange={(e) => setNome(e.target.value)} className="w-56"
        placeholder={area ? 'Nome (Entrada, Salão…)' : 'Nome opcional (Armário, Mesa…)'}
        onKeyDown={(e) => { if (e.key === 'Enter' && ok) onCriar(nome.trim()); if (e.key === 'Escape') onCancelar() }} />
      <Button size="sm" disabled={!ok} onClick={() => onCriar(nome.trim())}>Criar</Button>
      <Button size="sm" variant="outline" onClick={onCancelar}>Cancelar</Button>
      {problema && <span className="text-xs text-destructive">{problema}</span>}
    </div>
  )
}

// Mapa da cena: grade com áreas (retângulos) e participantes em células.
// Clique num participante para abrir/fechar o card (vários ao mesmo tempo); o card de quem está na vez abre sozinho.
// Arraste para mudar de célula ou tirá-lo do mapa. No modo "Editar mapa", desenhe áreas ou obstáculos na grade.
export function Mapa({
  mapa, areas, obstaculos, participantes, acoes, onCriarMapa, onExcluirMapa, onPosicionar,
  onCriarArea, onExcluirArea, onCriarObstaculo, onExcluirObstaculo,
}: {
  mapa: TurnoMapa | null
  areas: TurnoArea[]
  obstaculos: TurnoObstaculo[]
  participantes: Part[]
  acoes: Acoes
  onCriarMapa: (largura: number, altura: number) => void
  onExcluirMapa: () => void
  onPosicionar: (participanteId: string, pos: Pos | null) => void
  onCriarArea: (area: Ret & { nome: string }) => void
  onExcluirArea: (id: string) => void
  onCriarObstaculo: (obstaculo: Ret & { nome: string }) => void
  onExcluirObstaculo: (id: string) => void
}) {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }))
  const grade = useRef<HTMLDivElement>(null)
  const [abertos, setAbertos] = useState<Set<string>>(new Set())
  const [confirmando, setConfirmando] = useState(false)
  const [arrastando, setArrastando] = useState<Part | null>(null)
  const [alvo, setAlvo] = useState<Pos | null>(null)
  const [editando, setEditando] = useState(false)
  const [pendente, setPendente] = useState<Ret | null>(null)
  const [ferramenta, setFerramenta] = useState<Ferramenta>('area')

  const suaVez = (p: Part) => acoes.emAndamento && !!p.ordem && p.ordem === acoes.ordemAtual
  const vezId = participantes.find(suaVez)?.id ?? null
  // Card de quem está na vez: aberto por padrão; se fechado, só volta quando a vez mudar.
  const [fechouDaVez, setFechouDaVez] = useState(false)
  const [vezAnterior, setVezAnterior] = useState(vezId)
  if (vezAnterior !== vezId) { setVezAnterior(vezId); setFechouDaVez(false) }

  const aberto = (p: Part) => abertos.has(p.id) || (p.id === vezId && !fechouDaVez)
  const alternar = (p: Part) => {
    const novo = new Set(abertos)
    if (aberto(p)) {
      novo.delete(p.id)
      if (p.id === vezId) setFechouDaVez(true)
    } else if (p.id === vezId) {
      setFechouDaVez(false)
    } else {
      novo.add(p.id)
    }
    setAbertos(novo)
  }

  const noMapa = mapa ? participantes.filter((p) => p.pos) : []
  const fora = participantes.filter((p) => !mapa || !p.pos)
  const cards = participantes.filter(aberto)
  const ocupante = (c: Pos) => noMapa.find((p) => p.pos!.x === c.x && p.pos!.y === c.y)
  const livre = (c: Pos, id: string) => {
    const o = ocupante(c)
    return (!o || o.id === id) && !obstaculos.some((b) => dentro(b, c))
  }
  // Por que o retângulo desenhado não pode ser criado (null = pode).
  const motivo = (r: Ret): string | null => {
    if (ferramenta === 'area') {
      const a = sobrepoe(r, areas)
      return a ? `Sobrepõe "${a.nome}".` : null
    }
    if (sobrepoe(r, obstaculos)) return 'Sobrepõe outro obstáculo.'
    if (noMapa.some((p) => dentro(r, p.pos!))) return 'Há participantes nessas células.'
    return null
  }

  // Célula sob o ponteiro (só quando ele está sobre a parte visível do mapa).
  const celula = (e: DragMoveEvent | DragEndEvent): Pos | null => {
    const el = grade.current
    if (!mapa || !el || e.over?.id !== 'mapa') return null
    const ini = e.activatorEvent as PointerEvent
    const r = el.getBoundingClientRect()
    const x = Math.floor((ini.clientX + e.delta.x - r.left) / CELULA)
    const y = Math.floor((ini.clientY + e.delta.y - r.top) / CELULA)
    return x >= 0 && y >= 0 && x < mapa.largura && y < mapa.altura ? { x, y } : null
  }

  const aoMover = (e: DragMoveEvent) => {
    const c = celula(e)
    setAlvo((a) => (a?.x === c?.x && a?.y === c?.y ? a : c))
  }

  const aoSoltar = (e: DragEndEvent) => {
    const id = String(e.active.id)
    const atual = participantes.find((p) => p.id === id)?.pos ?? null
    const c = celula(e)
    setArrastando(null)
    setAlvo(null)
    if (e.over?.id === 'fora') {
      if (atual) onPosicionar(id, null)
    } else if (c && livre(c, id) && (atual?.x !== c.x || atual?.y !== c.y)) {
      onPosicionar(id, c)
    }
  }

  const sairDaEdicao = () => { setEditando(false); setPendente(null) }

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold">🗺️ Mapa da cena{mapa && <span className="ml-2 text-xs font-normal text-muted-foreground">{mapa.largura} × {mapa.altura}</span>}</h2>
        {mapa && (
          <div className="flex flex-wrap gap-1.5">
            <Button variant={editando ? 'default' : 'outline'} size="sm" onClick={() => (editando ? sairDaEdicao() : setEditando(true))}>
              <PencilRuler /> {editando ? 'Concluir edição' : 'Editar mapa'}
            </Button>
            {confirmando ? (
              <>
                <Button variant="destructive" size="sm" onClick={() => { setConfirmando(false); sairDaEdicao(); onExcluirMapa() }}>Excluir mapa, áreas e posições</Button>
                <Button variant="outline" size="sm" onClick={() => setConfirmando(false)}>Cancelar</Button>
              </>
            ) : (
              <Button variant="ghost" size="sm" onClick={() => setConfirmando(true)} className="hover:text-destructive"><Trash2 /> Excluir mapa</Button>
            )}
          </div>
        )}
      </div>

      {editando && (pendente ? (
        <NomearRet r={pendente} ferramenta={ferramenta} problema={motivo(pendente)} onCancelar={() => setPendente(null)}
          onCriar={(nome) => {
            (ferramenta === 'area' ? onCriarArea : onCriarObstaculo)({ nome, ...pendente })
            setPendente(null)
          }} />
      ) : (
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-lg border p-0.5">
            {(['area', 'obstaculo'] as const).map((f) => (
              <Button key={f} size="sm" variant={ferramenta === f ? 'secondary' : 'ghost'} onClick={() => setFerramenta(f)}>
                {f === 'area' ? 'Área' : 'Obstáculo'}
              </Button>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            {ferramenta === 'area'
              ? 'Clique e arraste na grade para desenhar uma área.'
              : 'Clique e arraste para marcar células bloqueadas (armário, mesa…). Podem ficar dentro de áreas.'}
            {' '}Use a lixeira para excluir.
          </p>
        </div>
      ))}

      <DndContext sensors={sensors} collisionDetection={pointerWithin}
        onDragStart={(e) => setArrastando(participantes.find((p) => p.id === e.active.id) ?? null)}
        onDragMove={aoMover} onDragEnd={aoSoltar}
        onDragCancel={() => { setArrastando(null); setAlvo(null) }}>
        {mapa ? (
          <Grade mapa={mapa} areas={areas} obstaculos={obstaculos} grade={grade}
            alvo={alvo} alvoLivre={!!alvo && !!arrastando && livre(alvo, arrastando.id)}
            editando={editando} pendente={pendente} motivo={motivo} onDesenhar={setPendente}
            onExcluirArea={onExcluirArea} onExcluirObstaculo={onExcluirObstaculo}>
            {noMapa.map((p) => (
              <Arrastavel key={p.id} p={p} desativado={editando} onClick={() => alternar(p)}
                className="z-10 flex items-center justify-center"
                style={{ gridColumn: p.pos!.x + 1, gridRow: p.pos!.y + 1 }}>
                <Icone p={p} className={cn(
                  'size-10 rounded-full transition-shadow',
                  suaVez(p) && 'ring-2 ring-primary',
                  aberto(p) && 'ring-2 ring-foreground',
                )} />
              </Arrastavel>
            ))}
          </Grade>
        ) : (
          <CriarMapa onCriar={onCriarMapa} />
        )}

        <ForaDoMapa vazio={fora.length === 0}>
          {fora.map((p) => (
            <Arrastavel key={p.id} p={p} desativado={editando} onClick={() => alternar(p)}
              className={cn('flex items-center gap-1.5 rounded-full border bg-card py-0.5 pr-2.5 pl-0.5 text-xs hover:border-primary',
                suaVez(p) && 'border-primary', aberto(p) && 'ring-2 ring-foreground')}>
              <Icone p={p} className="size-6 rounded-full text-sm" />{p.nome}
            </Arrastavel>
          ))}
        </ForaDoMapa>

        <DragOverlay>
          {arrastando && <Icone p={arrastando} className="size-10 rounded-full shadow-xl ring-2 ring-primary" />}
        </DragOverlay>
      </DndContext>

      {cards.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-3">
          {cards.map((p) => (
            <CardParticipante key={p.id}
              p={p}
              suaVez={suaVez(p)}
              onFicha={p.tipo === 'token' ? () => acoes.onFicha(p) : undefined}
              onRemover={p.tipo === 'token' ? () => acoes.onRemoverToken(p) : undefined}
            />
          ))}
        </div>
      )}
    </section>
  )
}
