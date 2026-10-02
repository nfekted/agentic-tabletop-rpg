import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, Play, Plus, Swords, Square, StepForward } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { StatusEditor } from '@/features/fichas/StatusEditor'
import { useJogadores, useSessao, useTokens, useTurno } from '@/hooks/queries'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { TurnoEstado, TurnoToken } from '@/lib/types'
import { Areas } from './Areas'
import { FilaIniciativa } from './FilaIniciativa'
import type { Part } from './Participante'

function FichaTokenDialog({ token, onFechar, onSalvar }: {
  token: TurnoToken; onFechar: () => void; onSalvar: (f: TurnoToken['ficha_dados']) => void
}) {
  const [f, setF] = useState(token.ficha_dados)
  return (
    <Dialog open onOpenChange={(o) => !o && onFechar()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{token.tipo_icone} {token.nome_exibicao}</DialogTitle>
          <DialogDescription>Cópia usada neste combate — editar aqui não altera o token original.</DialogDescription>
        </DialogHeader>
        <Textarea rows={10} value={f.conteudo} onChange={(e) => setF({ ...f, conteudo: e.target.value })} className="font-mono text-[13px]" />
        <StatusEditor status={f.status} onChange={(status) => setF({ ...f, status })} />
        <DialogFooter>
          <Button variant="outline" onClick={onFechar}>Cancelar</Button>
          <Button onClick={() => { onSalvar(f); onFechar() }}>Salvar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function TurnoView() {
  const qc = useQueryClient()
  const { data: estado } = useTurno()
  const { data: jogadores = [] } = useJogadores()
  const { data: sessao } = useSessao()
  const { data: catalogo } = useTokens()
  const [cat, setCat] = useState<string>('')
  const [arq, setArq] = useState<string>('')
  const [fichaToken, setFichaToken] = useState<string | null>(null)

  // Toda ação do turno devolve o estado completo (ou { ok, mensagem, ...estado }).
  const acao = useMutation({
    mutationFn: (fn: () => Promise<TurnoEstado & { ok?: boolean; mensagem?: string }>) => fn(),
    onSuccess: (r) => {
      qc.setQueryData(['turno'], { ativo: r.ativo, turno: r.turno, empates: r.empates })
      if (r.mensagem) (r.ok === false ? toast.warning : toast)(r.mensagem.replaceAll('**', ''))
    },
  })
  const run = (fn: () => Promise<TurnoEstado & { ok?: boolean; mensagem?: string }>) => acao.mutate(fn)

  if (!estado) return <p className="text-sm text-muted-foreground">Carregando…</p>

  if (!estado.ativo || !estado.turno)
    return (
      <div className="mx-auto flex max-w-md flex-col items-center gap-3 py-16 text-center">
        <Swords className="size-12 text-primary" />
        <h1 className="text-xl font-semibold">Modo por turnos</h1>
        <p className="text-sm text-muted-foreground">
          Gestão de cenas e combate: áreas, ordem de iniciativa e tokens de inimigos, NPCs e itens.
        </p>
        <Button size="lg" onClick={() => run(() => api.post('/turno/iniciar'))}><Play /> Iniciar modo por turnos</Button>
      </div>
    )

  const t = estado.turno
  const participantes: Part[] = [
    ...t.personagens.map((p): Part => ({
      id: p.id, tipo: 'personagem', nome: p.nome, ordem: p.ordem,
      jogador: jogadores.find((j) => j.nome === p.nome), fala: sessao?.ultima_fala[p.nome],
    })),
    ...t.tokens.map((k): Part => ({
      id: k.id, tipo: 'token', nome: k.nome_exibicao, ordem: k.ordem, token: k,
      imagem: catalogo?.[k.categoria]?.arquivos.find((a) => a.arquivo === k.arquivo)?.tem_imagem,
    })),
  ]
  const token = t.tokens.find((k) => k.id === fichaToken)
  const arquivos = cat ? (catalogo?.[cat]?.arquivos ?? []) : []

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="mr-auto text-xl font-semibold">⚔️ Modo por turnos</h1>
        <Button disabled={estado.empates.length > 0 || acao.isPending} onClick={() => run(() => api.post('/turno/proxima'))}>
          {t.em_andamento ? <StepForward /> : <Play />} {t.em_andamento ? 'Próxima ação' : 'Iniciar combate'}
        </Button>
        <Button variant="outline" onClick={() => run(() => api.del('/turno'))}><Square /> Encerrar modo</Button>
      </div>
      {estado.empates.length > 0 && (
        <p className="flex items-center gap-2 rounded-lg border border-amber-400/50 bg-amber-400/10 p-2 text-sm text-amber-200">
          <AlertTriangle className="size-4" /> Empate na(s) ordem(ns) {estado.empates.join(', ')}. Defina ordens distintas.
        </p>
      )}

      <div className="grid gap-5 xl:grid-cols-[22rem_1fr]">
        <div className="space-y-4">
          <FilaIniciativa
            participantes={participantes} emAndamento={t.em_andamento} ordemAtual={t.ordem_atual}
            onSalvar={(ids) => run(() => api.put('/turno/fila', { ids }))}
          />
          <section className="space-y-2 rounded-2xl border bg-card p-4">
            <h2 className="font-semibold">👾 Adicionar token ao combate</h2>
            <div className="flex flex-wrap gap-1.5">
              <Select value={cat} onValueChange={(v) => { setCat(v ?? ''); setArq('') }}>
                <SelectTrigger className="min-w-28 flex-1"><SelectValue placeholder="Categoria" /></SelectTrigger>
                <SelectContent>
                  {Object.entries(catalogo ?? {}).map(([id, c]) => <SelectItem key={id} value={id}>{c.rotulo}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={arq} onValueChange={(v) => setArq(v ?? '')} disabled={!cat}>
                <SelectTrigger className="min-w-28 flex-1"><SelectValue placeholder="Token" /></SelectTrigger>
                <SelectContent>
                  {arquivos.map((a) => <SelectItem key={a.arquivo} value={a.arquivo}>{a.arquivo.replace(/\.txt$/, '')}</SelectItem>)}
                </SelectContent>
              </Select>
              <Button variant="secondary" disabled={!arq} onClick={() => run(() => api.post('/turno/tokens', { categoria: cat, arquivo: arq }))}>
                <Plus /> Adicionar
              </Button>
            </div>
          </section>
        </div>

        <Areas
          areas={t.areas}
          participantes={participantes}
          acoes={{
            ordemAtual: t.ordem_atual, emAndamento: t.em_andamento,
            onFicha: (p) => setFichaToken(p.id),
            onRemoverToken: (p) => run(() => api.del(`/turno/tokens/${p.id}`)),
          }}
          onCriar={(nome) => run(() => api.post('/turno/areas', { nome }))}
          onExcluir={(id) => run(() => api.del(`/turno/areas/${id}`))}
          onMover={(pid, areaId) =>
            run(() => areaId
              ? api.put(`/turno/areas/${areaId}/participantes`, { participante_id: pid })
              : api.del(`/turno/participantes/${pid}/area`))}
        />
      </div>

      {token && (
        <FichaTokenDialog
          key={token.id} token={token} onFechar={() => setFichaToken(null)}
          onSalvar={(f) => run(() => api.put(`/turno/tokens/${token.id}/ficha`, f))}
        />
      )}
    </div>
  )
}
