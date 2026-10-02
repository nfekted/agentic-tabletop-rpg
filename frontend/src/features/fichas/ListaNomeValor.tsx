import { Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { ParNomeValor } from '@/lib/types'

// Lista de pares nome/valor (Atributos e Perícias). Linhas sem nome não são salvas.
export function ListaNomeValor({
  titulo, itens, onChange, rotuloAdicionar, exemploNome, exemploValor,
}: {
  titulo: string
  itens: ParNomeValor[]
  onChange: (l: ParNomeValor[]) => void
  rotuloAdicionar: string
  exemploNome: string
  exemploValor: string
}) {
  const set = (i: number, patch: Partial<ParNomeValor>) =>
    onChange(itens.map((p, k) => (k === i ? { ...p, ...patch } : p)))
  const semNome = itens.some((p) => !p.nome.trim())
  return (
    <section className="space-y-2 rounded-xl border p-3">
      <h3 className="text-sm font-semibold">{titulo}</h3>
      {itens.length === 0 && <p className="text-sm text-muted-foreground">Nada cadastrado ainda.</p>}
      {itens.map((p, i) => (
        <div key={i} className="grid grid-cols-[1fr_7rem_2rem] items-center gap-2">
          <Input value={p.nome} placeholder={`Ex.: ${exemploNome}`} aria-label="Nome" aria-invalid={!p.nome.trim()}
            onChange={(e) => set(i, { nome: e.target.value })} />
          <Input value={p.valor} placeholder={`Ex.: ${exemploValor}`} aria-label="Valor"
            onChange={(e) => set(i, { valor: e.target.value })} />
          <Button variant="ghost" size="icon-sm" aria-label="Remover" onClick={() => onChange(itens.filter((_, k) => k !== i))}>
            <Trash2 />
          </Button>
        </div>
      ))}
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">{semNome ? 'Linhas sem nome não são salvas.' : 'Nome · valor'}</p>
        <Button variant="outline" size="sm" onClick={() => onChange([...itens, { nome: '', valor: '' }])}>
          <Plus /> {rotuloAdicionar}
        </Button>
      </div>
    </section>
  )
}
