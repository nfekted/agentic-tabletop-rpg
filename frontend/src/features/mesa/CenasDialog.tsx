import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useAcao, useCenas } from '@/hooks/queries'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

// Cenas pré-cadastradas (arquivos/cenas): usar no campo de mensagem, criar a partir dele ou excluir.
export function CenasDialog({
  aberto, onFechar, textoAtual, onUsar,
}: { aberto: boolean; onFechar: () => void; textoAtual: string; onUsar: (t: string) => void }) {
  const { data: cenas = [] } = useCenas()
  const [sel, setSel] = useState<string | null>(null)
  const [nome, setNome] = useState('')

  const usar = useAcao(async (n: string) => {
    const c = await api.get<{ conteudo: string }>(`/cenas/${encodeURIComponent(n)}`)
    onUsar(c.conteudo)
    onFechar()
  })
  const criar = useAcao(
    () => api.post('/cenas', { nome, conteudo: textoAtual }),
    [['cenas']],
    () => { setNome(''); return 'Cena salva.' },
  )
  const excluir = useAcao(
    (n: string) => api.del(`/cenas/${encodeURIComponent(n)}`),
    [['cenas']],
    () => { setSel(null); return 'Cena excluída.' },
  )

  return (
    <Dialog open={aberto} onOpenChange={(o) => !o && onFechar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Cenas pré-cadastradas</DialogTitle>
          <DialogDescription>Reaproveite textos prontos, como a lista de itens de uma loja.</DialogDescription>
        </DialogHeader>

        <div className="max-h-48 space-y-1 overflow-y-auto">
          {cenas.length === 0 && <p className="text-sm text-muted-foreground">Nenhuma cena salva ainda.</p>}
          {cenas.map((c) => (
            <button
              key={c}
              onClick={() => setSel(c)}
              className={cn(
                'w-full rounded-lg border px-3 py-1.5 text-left text-sm hover:bg-muted',
                sel === c && 'border-primary bg-muted',
              )}
            >
              {c}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <Button disabled={!sel || usar.isPending} onClick={() => sel && usar.mutate(sel)} className="flex-1">
            Usar no campo de mensagem
          </Button>
          <Button
            variant="outline"
            size="icon"
            disabled={!sel || excluir.isPending}
            onClick={() => sel && excluir.mutate(sel)}
            aria-label="Excluir cena"
          >
            <Trash2 />
          </Button>
        </div>

        <div className="space-y-2 border-t pt-3">
          <p className="text-sm font-medium">Salvar a mensagem atual como nova cena</p>
          <div className="flex gap-2">
            <Input placeholder="Nome da cena" value={nome} onChange={(e) => setNome(e.target.value)} />
            <Button
              variant="secondary"
              disabled={!nome.trim() || !textoAtual.trim() || criar.isPending}
              onClick={() => criar.mutate()}
            >
              Salvar
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
