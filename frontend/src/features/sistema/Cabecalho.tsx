import { Loader2, Play, Square, XCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAcao, useAcaoMestre, useRegras, useSessao } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { AcaoResposta } from '@/lib/types'
import { useUi } from '@/lib/ui-context'
import { ModoTeste } from './ModoTeste' // MODO-TESTE

export function Cabecalho() {
  const { abrir } = useUi()
  const { data: s } = useSessao()
  const { data: regras } = useRegras()
  const iniciar = useAcaoMestre(() => api.post<AcaoResposta>('/rodada/iniciar'))
  const finalizar = useAcaoMestre(() => api.post<AcaoResposta>('/rodada/finalizar'))
  const ativar = useAcao((n: string) => api.put('/regras/ativa', { nome: n }), [['regras']], 'Conjunto de regras trocado.')
  const ativa = !!s?.rodada_ativa

  return (
    <header className="sticky top-0 z-30 flex flex-wrap items-center gap-2 border-b bg-background/85 px-4 py-2.5 backdrop-blur">
      <h1 className="mr-1 text-lg font-semibold">🎲 Mesa de RPG</h1>
      <Badge variant={ativa ? 'default' : 'secondary'}>{ativa ? '● Rodada em andamento' : 'Sem rodada'}</Badge>

      <div className="ml-auto flex flex-wrap items-center gap-2">
        {regras?.ativa && (
          <Select value={regras.ativa} onValueChange={(v) => v && v !== regras.ativa && ativar.mutate(v)}>
            <SelectTrigger size="sm" aria-label="Conjunto de regras ativo" className="max-w-40"><SelectValue /></SelectTrigger>
            <SelectContent>
              {regras.arquivos.map((a) => <SelectItem key={a} value={a}>📜 {a.replace(/\.txt$/, '')}</SelectItem>)}
            </SelectContent>
          </Select>
        )}
        <ModoTeste /> {/* MODO-TESTE */}
        {!ativa ? (
          <Button size="sm" disabled={iniciar.isPending} onClick={() => iniciar.mutate()}><Play /> Iniciar rodada</Button>
        ) : (
          <>
            <Button size="sm" disabled={finalizar.isPending} onClick={() => finalizar.mutate()}>
              {finalizar.isPending ? <Loader2 className="animate-spin" /> : <Square />}
              {finalizar.isPending ? 'Consolidando memória…' : 'Finalizar rodada'}
            </Button>
            <Button size="sm" variant="outline" disabled={finalizar.isPending} onClick={() => abrir({ tipo: 'cancelar-rodada' })}>
              <XCircle /> Cancelar
            </Button>
          </>
        )}
      </div>
    </header>
  )
}
