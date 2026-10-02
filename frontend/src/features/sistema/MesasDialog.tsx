import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Download, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useAcao, useMesasSalvas } from '@/hooks/queries'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

export function MesasDialog({ onFechar }: { onFechar: () => void }) {
  const qc = useQueryClient()
  const { data: mesas = [] } = useMesasSalvas()
  const [nome, setNome] = useState('')
  const [sel, setSel] = useState<string | null>(null)
  const [confirmar, setConfirmar] = useState(false)

  const existe = mesas.some((m) => m.nome === nome.trim())
  const salvar = useAcao(
    () => api.post<{ mensagem: string }>('/mesas', { nome }),
    [['mesas']], (r) => r.mensagem,
  )
  const restaurar = useAcao(
    () => api.post<{ mensagem: string }>(`/mesas/${encodeURIComponent(sel!)}/restaurar`),
    [], (r) => r.mensagem,
  )

  return (
    <Dialog open onOpenChange={(o) => !o && onFechar()}>
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
                <button key={m.nome} onClick={() => { setSel(m.nome); setConfirmar(false) }}
                  className={cn('w-full rounded-lg border px-3 py-1.5 text-left text-sm hover:bg-muted', sel === m.nome && 'border-primary bg-muted')}>
                  <span className="block">{m.nome}</span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(m.atualizada_em).toLocaleString('pt-BR')} · {(m.tamanho / 1024).toFixed(0)} KB
                  </span>
                </button>
              ))}
            </div>
            {sel && !confirmar && <Button variant="secondary" className="w-full" onClick={() => setConfirmar(true)}>Restaurar “{sel}”</Button>}
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
            <Input placeholder="Nome da mesa" value={nome} onChange={(e) => setNome(e.target.value)} />
            {existe && <p className="text-xs text-amber-300">Já existe uma mesa com esse nome — salvar vai sobrescrevê-la.</p>}
            <Button className="w-full" disabled={!nome.trim() || salvar.isPending} onClick={() => salvar.mutate()}>
              {existe ? 'Sobrescrever' : 'Salvar'}
            </Button>
            <p className="text-xs text-muted-foreground">
              O config.json (com a API Key) não entra no zip. Rodadas em andamento não são salvas.
            </p>
          </section>
        </div>
      </DialogContent>
    </Dialog>
  )
}
