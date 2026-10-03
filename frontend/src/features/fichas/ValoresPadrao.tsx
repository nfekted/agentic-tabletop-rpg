import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useUi } from '@/lib/ui-context'
import type { ParNomeValor, Status } from '@/lib/types'

export function AvisoSemPadrao() {
  const { abrir } = useUi()
  return (
    <div className="flex flex-col items-start gap-2 rounded-xl border border-dashed p-3 text-sm text-muted-foreground">
      <p>Nenhum padrão de status e atributos cadastrado. Configure-o uma vez para todos os personagens.</p>
      <Button variant="outline" size="sm" onClick={() => abrir({ tipo: 'padrao-ficha' })}>Configurar padrão</Button>
    </div>
  )
}

// Número que aceita o campo vazio enquanto se digita (vazio vale 0 no valor guardado).
export function NumInput({ valor, onChange, rotulo }: { valor: number; onChange: (n: number) => void; rotulo: string }) {
  const [texto, setTexto] = useState(String(valor))
  const mostrado = (texto === '' ? 0 : Number(texto)) === valor ? texto : String(valor)
  return (
    <Input type="number" value={mostrado} aria-label={rotulo}
      onChange={(e) => { setTexto(e.target.value); onChange(e.target.value === '' ? 0 : Number(e.target.value)) }} />
  )
}

// Valores dos status definidos no padrão: nome e cor são fixos, só atual/máximo são editáveis.
export function StatusValores({ status, onChange }: { status: Status[]; onChange: (s: Status[]) => void }) {
  const set = (i: number, patch: Partial<Status>) => onChange(status.map((s, k) => (k === i ? { ...s, ...patch } : s)))
  return (
    <div className="space-y-2">
      {status.map((s, i) => (
        <div key={s.nome} className="grid grid-cols-[1fr_4.5rem_4.5rem] items-center gap-2">
          <span className="flex items-center gap-2 text-sm"><span className="size-3 rounded-full" style={{ background: s.cor }} />{s.nome}</span>
          <NumInput valor={s.valor_atual} onChange={(n) => set(i, { valor_atual: n })} rotulo={`${s.nome}: valor atual`} />
          <NumInput valor={s.valor_max} onChange={(n) => set(i, { valor_max: n })} rotulo={`${s.nome}: valor máximo`} />
        </div>
      ))}
      <p className="text-xs text-muted-foreground">Status · atual · máximo</p>
    </div>
  )
}

export function AtributosValores({ atributos, onChange }: { atributos: ParNomeValor[]; onChange: (a: ParNomeValor[]) => void }) {
  return (
    <section className="space-y-2 rounded-xl border p-3">
      <h3 className="text-sm font-semibold">Atributos</h3>
      {atributos.map((a, i) => (
        <div key={a.nome} className="grid grid-cols-[1fr_7rem] items-center gap-2">
          <span className="text-sm">{a.nome}</span>
          <Input value={a.valor} aria-label={`${a.nome}: valor`}
            onChange={(e) => onChange(atributos.map((x, k) => (k === i ? { ...x, valor: e.target.value } : x)))} />
        </div>
      ))}
    </section>
  )
}
