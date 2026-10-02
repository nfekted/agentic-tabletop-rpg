import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Star, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { useAcao, useRegras } from '@/hooks/queries'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

function Editor({ arquivo, ativa }: { arquivo: string; ativa: boolean }) {
  const { data } = useQuery({
    queryKey: ['regra', arquivo], gcTime: 0,
    queryFn: () => api.get<{ conteudo: string }>(`/regras/${encodeURIComponent(arquivo)}`),
  })
  const [texto, setTexto] = useState<string | null>(null)
  const atual = texto ?? data?.conteudo ?? ''

  const salvar = useAcao(() => api.put(`/regras/${encodeURIComponent(arquivo)}`, { conteudo: atual }), [['regra', arquivo]], 'Regras salvas.')
  const ativar = useAcao(() => api.put('/regras/ativa', { nome: arquivo }), [['regras']], `${arquivo} agora é o conjunto ativo.`)
  const excluir = useAcao(() => api.del(`/regras/${encodeURIComponent(arquivo)}`), [['regras']], 'Conjunto excluído.')

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-2">
      <Textarea value={atual} onChange={(e) => setTexto(e.target.value)} className="min-h-64 flex-1 font-mono text-[13px]" disabled={!data} />
      <div className="flex flex-wrap gap-2">
        <Button disabled={salvar.isPending || texto === null} onClick={() => salvar.mutate()}>Salvar</Button>
        <Button variant="secondary" disabled={ativa || ativar.isPending} onClick={() => ativar.mutate()}><Star /> Usar agora</Button>
        <Button variant="outline" className="ml-auto" disabled={excluir.isPending} onClick={() => excluir.mutate()}><Trash2 /> Excluir</Button>
      </div>
    </div>
  )
}

export function RegrasDialog({ onFechar }: { onFechar: () => void }) {
  const { data } = useRegras()
  const [sel, setSel] = useState<string | null>(null)
  const [novo, setNovo] = useState('')
  const arquivos = data?.arquivos ?? []
  const atual = sel && arquivos.includes(sel) ? sel : (data?.ativa ?? arquivos[0] ?? null)

  const criar = useAcao(
    () => api.post<{ arquivo: string }>('/regras', { nome: novo }),
    [['regras']], 'Conjunto criado.',
  )

  return (
    <Dialog open onOpenChange={(o) => !o && onFechar()}>
      <DialogContent className="flex h-[80vh] flex-col sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>📜 Conjuntos de regras</DialogTitle>
          <DialogDescription>Só o conjunto ativo (⭐) é enviado no prompt dos jogadores.</DialogDescription>
        </DialogHeader>
        <div className="flex min-h-0 flex-1 flex-col gap-3 sm:flex-row">
          <div className="space-y-2 sm:w-52 sm:shrink-0">
            <div className="max-h-40 space-y-1 overflow-y-auto sm:max-h-[50vh]">
              {arquivos.map((a) => (
                <button key={a} onClick={() => setSel(a)}
                  className={cn('flex w-full items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-left text-sm hover:bg-muted', atual === a && 'border-primary bg-muted')}>
                  {data?.ativa === a && <Star className="size-3.5 shrink-0 fill-primary text-primary" />}
                  <span className="truncate">{a}</span>
                </button>
              ))}
            </div>
            <div className="flex gap-1.5">
              <Input value={novo} onChange={(e) => setNovo(e.target.value)} placeholder="Novo conjunto" />
              <Button variant="secondary" disabled={!novo.trim() || criar.isPending}
                onClick={() => criar.mutate(undefined, { onSuccess: (r) => { setNovo(''); setSel(r.arquivo) } })}>
                Criar
              </Button>
            </div>
          </div>
          {atual && <Editor key={atual} arquivo={atual} ativa={data?.ativa === atual} />}
        </div>
      </DialogContent>
    </Dialog>
  )
}
