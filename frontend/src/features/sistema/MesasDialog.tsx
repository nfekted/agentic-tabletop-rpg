import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Download, Trash2, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DialogAberto } from '@/components/DialogAberto'
import { DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useAcao, useMesaAtual, useMesasSalvas } from '@/hooks/queries'
import { ImportarBase } from './ImportarBase'
import { api } from '@/lib/api'
import { useUi } from '@/lib/ui-context'
import { cn } from '@/lib/utils'

export function MesasDialog({ onFechar }: { onFechar: () => void }) {
  const qc = useQueryClient()
  const { abrir } = useUi()
  const { data: mesas = [] } = useMesasSalvas()
  const mesa = useMesaAtual().data?.nome ?? ''
  const [nome, setNome] = useState('')
  const [sel, setSel] = useState<string | null>(null)
  const selAutosave = mesas.find((m) => m.nome === sel)?.autosave ?? false
  const [confirmar, setConfirmar] = useState(false)
  const [excluindo, setExcluindo] = useState(false)
  const [perigo, setPerigo] = useState<'reiniciar' | 'resetar' | 'importar' | null>(null)

  const existe = mesas.some((m) => m.nome === `${mesa}_${nome.trim()}`)
  const salvar = useAcao(
    () => api.post<{ mensagem: string }>('/mesas', { nome }),
    [['mesas']], (r) => r.mensagem,
  )
  const restaurar = useAcao(
    () => api.post<{ mensagem: string }>(`/mesas/${encodeURIComponent(sel!)}/restaurar`),
    [], (r) => r.mensagem,
  )

  const excluir = useAcao(
    () => api.del<{ mensagem: string }>(`/mesas/${encodeURIComponent(sel!)}`),
    [['mesas']], (r) => r.mensagem,
  )

  const reiniciar = useAcao(() => api.post<{ mensagem: string }>('/mesas/reiniciar'), [], (r) => r.mensagem)
  const resetar = useAcao(() => api.post<{ mensagem: string }>('/mesas/resetar'), [], (r) => r.mensagem)

  return (
    <DialogAberto onFechar={onFechar}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>💾 Salvar / Restaurar mesa</DialogTitle>
          <DialogDescription>Backup completo da campanha em um .zip (fichas, regras, cenas, memórias, tokens e combate).</DialogDescription>
        </DialogHeader>
        <div className="grid gap-6 sm:grid-cols-2">
          <section className="space-y-3">
            <h3 className="flex items-center gap-1.5 font-medium"><Upload className="size-4" /> Restaurar mesa</h3>
            <div className="max-h-52 space-y-1 overflow-y-auto">
              {mesas.length === 0 && <p className="text-sm text-muted-foreground">Nenhuma mesa salva ainda.</p>}
              {mesas.map((m) => (
                <button key={m.nome} onClick={() => { setSel(m.nome); setConfirmar(false); setExcluindo(false) }}
                  className={cn('w-full rounded-lg border px-3 py-1.5 text-left text-sm hover:bg-muted', sel === m.nome && 'border-primary bg-muted')}>
                  <span className="block">
                    {m.nome}
                    {m.autosave && <span className="ml-2 rounded bg-primary/15 px-1.5 text-[10px] uppercase text-primary">autosave</span>}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(m.atualizada_em).toLocaleString('pt-BR')} · {(m.tamanho / 1024).toFixed(0)} KB
                  </span>
                </button>
              ))}
            </div>
            {sel && !confirmar && !excluindo && (
              <div className="flex gap-2">
                <Button variant="secondary" className="min-w-0 flex-1" onClick={() => setConfirmar(true)}>
                  <span className="truncate">Restaurar “{sel}”</span>
                </Button>
                <Button variant="outline" size="icon" aria-label="Excluir backup" className="hover:text-destructive" disabled={selAutosave}
                  title={selAutosave ? 'O autosave não pode ser excluído' : 'Excluir backup'} onClick={() => setExcluindo(true)}>
                  <Trash2 />
                </Button>
              </div>
            )}
            {sel && excluindo && (
              <div className="space-y-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm">
                <p>Excluir o backup <b>{sel}</b>? O arquivo é apagado do computador e <b>não dá para recuperar</b>.</p>
                <div className="flex gap-2">
                  <Button variant="destructive" size="sm" disabled={excluir.isPending}
                    onClick={() => excluir.mutate(undefined, { onSuccess: () => { setSel(null); setExcluindo(false) } })}>
                    Sim, excluir
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setExcluindo(false)}>Não</Button>
                </div>
              </div>
            )}
            {sel && confirmar && (
              <div className="space-y-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm">
                <p>Isso <b>substitui</b> tudo o que está na mesa agora. Continuar?</p>
                <div className="flex gap-2">
                  <Button variant="destructive" size="sm" disabled={restaurar.isPending}
                    onClick={() => restaurar.mutate(undefined, { onSuccess: () => { qc.invalidateQueries(); onFechar() } })}>
                    Sim, restaurar
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setConfirmar(false)}>Não</Button>
                </div>
              </div>
            )}
          </section>
          <section className="space-y-3">
            <h3 className="flex items-center gap-1.5 font-medium"><Download className="size-4" /> Salvar mesa</h3>
            {mesa ? (
              <p className="text-xs text-muted-foreground">
                Mesa atual: <b>{mesa}</b>. O arquivo será <b>{mesa}_{nome.trim() || '…'}.zip</b>
              </p>
            ) : (
              <p className="text-xs text-amber-300">
                Dê um nome à mesa antes de salvar.{' '}
                <button className="underline" onClick={() => abrir({ tipo: 'nome-mesa' })}>Nomear mesa</button>
              </p>
            )}
            <Input placeholder="Nome do backup" value={nome} onChange={(e) => setNome(e.target.value)} />
            {existe && <p className="text-xs text-amber-300">Já existe um backup com esse nome — salvar vai sobrescrevê-lo.</p>}
            <Button className="w-full" disabled={!mesa || !nome.trim() || salvar.isPending} onClick={() => salvar.mutate()}>
              {existe ? 'Sobrescrever' : 'Salvar'}
            </Button>
            <p className="text-xs text-muted-foreground">
              O config.json (com a API Key) não entra no zip. Rodadas em andamento não são salvas.
            </p>
          </section>
        </div>
        <div className="flex items-start justify-between gap-3 rounded-lg border p-3">
          <p className="text-sm">
            <b>Encerrar mesa</b>
            <span className="block text-xs text-muted-foreground">Fim de missão: compila a memória de cada personagem e, se quiser, gera o resumo da missão para a ficha. Não apaga nada.</span>
          </p>
          <Button variant="outline" size="sm" onClick={() => abrir({ tipo: 'encerrar-mesa' })}>Encerrar</Button>
        </div>
        <div className="space-y-3 rounded-lg border border-destructive/40 p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-destructive">Zona de perigo</p>
          {!perigo ? (
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm">
                  <b>Reiniciar mesa</b>
                  <span className="block text-xs text-muted-foreground">Mantém personagens, fichas, regras, cenas e tokens. Apaga só memórias, sessão e fila.</span>
                </p>
                <Button variant="outline" size="sm" onClick={() => setPerigo('reiniciar')}>Reiniciar</Button>
              </div>
              <div className="flex items-start justify-between gap-3 border-t pt-3">
                <p className="text-sm">
                  <b>Importar base</b>
                  <span className="block text-xs text-muted-foreground">Começa uma mesa nova a partir de um backup, trazendo só o que você escolher (personagens, regras, inimigos...).</span>
                </p>
                <Button variant="outline" size="sm" onClick={() => setPerigo('importar')}>Importar</Button>
              </div>
              <div className="flex items-start justify-between gap-3 border-t pt-3">
                <p className="text-sm">
                  <b>Resetar mesa</b>
                  <span className="block text-xs text-muted-foreground">Apaga tudo: personagens, memórias, cenas, tokens, itens e inimigos.</span>
                </p>
                <Button variant="destructive" size="sm" onClick={() => setPerigo('resetar')}>Resetar</Button>
              </div>
            </div>
          ) : perigo === 'importar' ? (
            <ImportarBase onCancelar={() => setPerigo(null)} onFeito={onFechar} />
          ) : (
            <div className="space-y-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm">
              {perigo === 'reiniciar' ? (
                <p>
                  Recomeça a campanha do zero <b>mantendo o cenário</b>: personagens, fichas, regras, cenas e tokens ficam.
                  Apaga só as memórias dos personagens (rodadas, cenas, resumos, métricas), a rodada em andamento, o
                  histórico e a fila. <b>Não é possível recuperar</b>; recomendamos criar um backup antes
                  (💾 Salvar / Restaurar mesa). Continuar?
                </p>
              ) : (
                <p>
                  Isso apaga <b>todos</b> os personagens, históricos, memórias, cenas, tokens, itens e inimigos.
                  Só as configurações da LLM são mantidas. <b>Não é possível recuperar</b>; recomendamos criar um backup
                  antes (💾 Salvar / Restaurar mesa). Continuar?
                </p>
              )}
              <div className="flex gap-2">
                <Button variant="destructive" size="sm" disabled={reiniciar.isPending || resetar.isPending}
                  onClick={() => (perigo === 'reiniciar' ? reiniciar : resetar).mutate(undefined, { onSuccess: () => { qc.invalidateQueries(); onFechar() } })}>
                  {perigo === 'reiniciar' ? 'Sim, reiniciar' : 'Sim, apagar tudo'}
                </Button>
                <Button variant="outline" size="sm" onClick={() => setPerigo(null)}>Não</Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </DialogAberto>
  )
}
