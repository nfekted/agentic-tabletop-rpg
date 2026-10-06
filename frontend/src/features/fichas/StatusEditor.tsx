import { Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { Status } from '@/lib/types'
import { NumInput } from './ValoresPadrao'
import { patchAt, removeAt } from '@/lib/utils'
import { InputCor } from '@/components/InputCor'

// Editor de status dinâmicos (vida, mana...): usado na ficha dos jogadores e na dos tokens do combate.
export function StatusEditor({ status, onChange }: { status: Status[]; onChange: (s: Status[]) => void }) {
  const set = (i: number, patch: Partial<Status>) =>
    onChange(patchAt(status, i, patch))
  return (
    <div className="space-y-2">
      {status.map((s, i) => (
        <div key={i} className="grid grid-cols-[1fr_4.5rem_4.5rem_2.5rem_2rem] items-center gap-2">
          <Input value={s.nome} onChange={(e) => set(i, { nome: e.target.value })} placeholder="Nome" aria-label="Nome do status" />
          <NumInput valor={s.valor_atual} onChange={(n) => set(i, { valor_atual: n })} rotulo="Valor atual" />
          <NumInput valor={s.valor_max} onChange={(n) => set(i, { valor_max: n })} rotulo="Valor máximo" />
          <InputCor value={s.cor} onChange={(cor) => set(i, { cor })} />
          <Button variant="ghost" size="icon-sm" onClick={() => onChange(removeAt(status, i))} aria-label="Remover status">
            <Trash2 />
          </Button>
        </div>
      ))}
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">Nome · atual · máximo · cor</p>
        <Button variant="outline" size="sm" onClick={() => onChange([...status, { nome: 'Novo status', valor_atual: 1, valor_max: 10, cor: '#32cd32' }])}>
          <Plus /> Status
        </Button>
      </div>
    </div>
  )
}
