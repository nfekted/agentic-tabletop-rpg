import { useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DialogAberto } from '@/components/DialogAberto'
import {
  DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useAcao, usePadraoFicha } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { PadraoFicha } from '@/lib/types'
import { Carregando } from '@/components/Carregando'
import { patchAt, removeAt } from '@/lib/utils'
import { InputCor } from '@/components/InputCor'

type Dados = Pick<PadraoFicha, 'status' | 'atributos'>

function Form({ inicial, onFechar }: { inicial: PadraoFicha; onFechar: () => void }) {
  const [d, setD] = useState<Dados>({ status: inicial.status, atributos: inicial.atributos })
  const salvar = useAcao(() => api.put('/padrao-ficha', d), [['padrao-ficha'], ['ficha'], ['jogadores'], ['ficha-md']], 'Padrão salvo.')
  const setStatus = (i: number, patch: Partial<Dados['status'][number]>) =>
    setD({ ...d, status: patchAt(d.status, i, patch) })

  return (
    <>
      {!inicial.configurado && (
        <p className="rounded-lg border border-dashed p-2 text-sm text-muted-foreground">
          Ao salvar o padrão pela primeira vez, os status e atributos já preenchidos nas fichas são descartados.
        </p>
      )}
      <div className="grid gap-3 md:grid-cols-2">
        <section className="space-y-2 rounded-xl border p-3">
          <h3 className="text-sm font-semibold">Status (atual / máximo)</h3>
          {d.status.map((s, i) => (
            <div key={i} className="grid grid-cols-[1fr_2.5rem_2rem] items-center gap-2">
              <Input value={s.nome} placeholder="Ex.: Vida" aria-label="Nome do status" onChange={(e) => setStatus(i, { nome: e.target.value })} />
              <InputCor value={s.cor} onChange={(cor) => setStatus(i, { cor })} />
              <Button variant="ghost" size="icon-sm" aria-label="Remover" onClick={() => setD({ ...d, status: removeAt(d.status, i) })}><Trash2 /></Button>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={() => setD({ ...d, status: [...d.status, { nome: '', cor: '#DC143C' }] })}><Plus /> Status</Button>
        </section>
        <section className="space-y-2 rounded-xl border p-3">
          <h3 className="text-sm font-semibold">Atributos</h3>
          {d.atributos.map((a, i) => (
            <div key={i} className="grid grid-cols-[1fr_2rem] items-center gap-2">
              <Input value={a.nome} placeholder="Ex.: Força" aria-label="Nome do atributo"
                onChange={(e) => setD({ ...d, atributos: patchAt(d.atributos, i, { nome: e.target.value }) })} />
              <Button variant="ghost" size="icon-sm" aria-label="Remover" onClick={() => setD({ ...d, atributos: removeAt(d.atributos, i) })}><Trash2 /></Button>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={() => setD({ ...d, atributos: [...d.atributos, { nome: '' }] })}><Plus /> Atributo</Button>
        </section>
      </div>
      <p className="text-xs text-muted-foreground">Linhas sem nome não são salvas. Renomear ou remover um item apaga o valor dele nas fichas.</p>
      <DialogFooter>
        <Button variant="outline" onClick={onFechar}>Cancelar</Button>
        <Button disabled={salvar.isPending} onClick={() => salvar.mutate(undefined, { onSuccess: onFechar })}>Salvar padrão</Button>
      </DialogFooter>
    </>
  )
}

export function PadraoFichaDialog({ onFechar }: { onFechar: () => void }) {
  const { data } = usePadraoFicha()
  return (
    <DialogAberto onFechar={onFechar}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Padrão de status e atributos</DialogTitle>
          <DialogDescription>Todos os personagens recebem estes status e atributos; na ficha, só falta preencher os valores.</DialogDescription>
        </DialogHeader>
        {data ? <Form inicial={data} onFechar={onFechar} /> : <Carregando />}
      </DialogContent>
    </DialogAberto>
  )
}
