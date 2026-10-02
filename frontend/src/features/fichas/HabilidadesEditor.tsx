import { Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { Habilidade, Habilidades } from '@/lib/types'

const BLOCOS = [
  { chave: 'habilidades', titulo: 'Habilidades', singular: 'Habilidade', exemplo: 'Camuflar', cor: 'border-l-sky-400' },
  { chave: 'poderes', titulo: 'Poderes', singular: 'Poder', exemplo: 'Golpe sísmico', cor: 'border-l-violet-400' },
  { chave: 'passivas', titulo: 'Passivas', singular: 'Passiva', exemplo: 'Visão no escuro', cor: 'border-l-emerald-400' },
] as const

export function HabilidadesEditor({ valor, onChange }: { valor: Habilidades; onChange: (h: Habilidades) => void }) {
  const setBloco = (chave: keyof Habilidades, lista: Habilidade[]) => onChange({ ...valor, [chave]: lista })
  return (
    <div className="space-y-4">
      {BLOCOS.map((b) => {
        const lista = valor[b.chave]
        const set = (i: number, patch: Partial<Habilidade>) =>
          setBloco(b.chave, lista.map((h, k) => (k === i ? { ...h, ...patch } : h)))
        return (
          <section key={b.chave} className={`space-y-2 rounded-xl border border-l-4 p-3 ${b.cor}`}>
            <h3 className="text-sm font-semibold">{b.titulo}</h3>
            {lista.length === 0 && <p className="text-sm text-muted-foreground">Nada cadastrado ainda.</p>}
            {lista.map((h, i) => (
              <div key={i} className="grid grid-cols-1 items-center gap-2 sm:grid-cols-[1fr_7rem_2fr_2rem]">
                <Input value={h.nome} placeholder={`Nome (ex.: ${b.exemplo})`} aria-label="Nome" aria-invalid={!h.nome.trim()}
                  onChange={(e) => set(i, { nome: e.target.value })} />
                <Input value={h.custo} placeholder="Custo" aria-label="Custo"
                  onChange={(e) => set(i, { custo: e.target.value })} />
                <Input value={h.descricao} placeholder="Descrição" aria-label="Descrição"
                  onChange={(e) => set(i, { descricao: e.target.value })} />
                <Button variant="ghost" size="icon-sm" aria-label="Remover" onClick={() => setBloco(b.chave, lista.filter((_, k) => k !== i))}>
                  <Trash2 />
                </Button>
              </div>
            ))}
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs text-muted-foreground">
                {lista.some((h) => !h.nome.trim()) ? 'Linhas sem nome não são salvas.' : 'Nome · custo · descrição'}
              </p>
              <Button variant="outline" size="sm" onClick={() => setBloco(b.chave, [...lista, { nome: '', custo: '', descricao: '' }])}>
                <Plus /> {b.singular}
              </Button>
            </div>
          </section>
        )
      })}
    </div>
  )
}
