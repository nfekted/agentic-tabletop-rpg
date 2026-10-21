import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { DialogAberto } from '@/components/DialogAberto'
import { DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { useAcao } from '@/hooks/queries'
import { api } from '@/lib/api'

export function AnotacoesDialog({ onFechar }: { onFechar: () => void }) {
  const { data } = useQuery({
    queryKey: ['anotacoes'], gcTime: 0,
    queryFn: () => api.get<{ conteudo: string }>('/anotacoes'),
  })
  const [texto, setTexto] = useState<string | null>(null)
  const alterado = texto !== null && texto !== data?.conteudo

  const salvar = useAcao(() => api.put('/anotacoes', { conteudo: texto }), [['anotacoes']], 'Anotações salvas.')

  // fechar também salva: anotação rápida não pode se perder
  const fechar = () => {
    if (alterado) api.put('/anotacoes', { conteudo: texto }).catch(() => {})
    onFechar()
  }

  return (
    <DialogAberto onFechar={fechar}>
      <DialogContent className="flex h-[70vh] flex-col sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>📝 Anotações do mestre</DialogTitle>
          <DialogDescription>Lembretes só seus (ex.: fórmulas de acerto e defesa). Os jogadores não veem. Salvo ao fechar e junto com a mesa.</DialogDescription>
        </DialogHeader>
        <Textarea
          value={texto ?? data?.conteudo ?? ''}
          onChange={(e) => setTexto(e.target.value)}
          disabled={!data}
          autoFocus
          className="min-h-0 flex-1 font-mono text-[13px]"
        />
        <div>
          <Button disabled={!alterado || salvar.isPending} onClick={() => salvar.mutate()}>Salvar</Button>
        </div>
      </DialogContent>
    </DialogAberto>
  )
}
