import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useAcao, useAcaoMestre } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { AcaoResposta } from '@/lib/types'

export function NovoJogadorDialog({ onFechar }: { onFechar: () => void }) {
  const [nome, setNome] = useState('')
  const criar = useAcao(() => api.post('/jogadores', { nome }), [['jogadores'], ['turno']], `${nome} entrou na mesa.`)
  const enviar = () => nome.trim() && criar.mutate(undefined, { onSuccess: onFechar })
  return (
    <Dialog open onOpenChange={(o) => !o && onFechar()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Adicionar jogador</DialogTitle>
          <DialogDescription>Use letras, números ou _ (sem espaços). O jogador nasce com uma ficha modelo.</DialogDescription>
        </DialogHeader>
        <Input autoFocus placeholder="Nome do jogador" value={nome} onChange={(e) => setNome(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && enviar()} />
        <DialogFooter>
          <Button variant="outline" onClick={onFechar}>Cancelar</Button>
          <Button disabled={!nome.trim() || criar.isPending} onClick={enviar}>Adicionar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function ExcluirJogadorDialog({ nome, onFechar }: { nome: string; onFechar: () => void }) {
  const excluir = useAcao(
    () => api.del(`/jogadores/${nome}`),
    [['jogadores'], ['sessao'], ['turno']], `${nome} foi excluído.`,
  )
  return (
    <Dialog open onOpenChange={(o) => !o && onFechar()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Excluir {nome}?</DialogTitle>
          <DialogDescription>
            Remove o jogador por completo: ficha, memória (rodadas, cenas e mesa), foto e presença no modo por turnos.
            Não dá para desfazer — se quiser garantir, salve a mesa antes.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onFechar}>Cancelar</Button>
          <Button variant="destructive" disabled={excluir.isPending} onClick={() => excluir.mutate(undefined, { onSuccess: onFechar })}>
            Excluir definitivamente
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function CancelarRodadaDialog({ onFechar }: { onFechar: () => void }) {
  const [motivo, setMotivo] = useState('')
  const cancelar = useAcaoMestre(() => api.post<AcaoResposta>('/rodada/cancelar', { motivo }))
  return (
    <Dialog open onOpenChange={(o) => !o && onFechar()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Cancelar rodada</DialogTitle>
          <DialogDescription>
            As memórias temporárias desta rodada vão para a pasta de logs (arquivos/rodadas_canceladas), junto com o motivo.
          </DialogDescription>
        </DialogHeader>
        <Input autoFocus placeholder="Motivo do cancelamento" value={motivo} onChange={(e) => setMotivo(e.target.value)} />
        <DialogFooter>
          <Button variant="outline" onClick={onFechar}>Voltar</Button>
          <Button variant="destructive" disabled={cancelar.isPending} onClick={() => cancelar.mutate(undefined, { onSuccess: onFechar })}>
            Cancelar rodada
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
