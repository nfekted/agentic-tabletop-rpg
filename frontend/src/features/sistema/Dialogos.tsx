import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DialogAberto } from '@/components/DialogAberto'
import {
  DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { FichaForm } from '@/features/fichas/FichaEditor'
import { useAcao, useAcaoMestre, useMesaAtual } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { AcaoResposta, Ficha } from '@/lib/types'

export function NovoJogadorDialog({ onFechar }: { onFechar: () => void }) {
  const [nome, setNome] = useState('')
  const [modo, setModo] = useState<'nome' | 'ia'>('nome')
  const [descricao, setDescricao] = useState('')
  const [gerada, setGerada] = useState<{ ficha: Ficha; versao: number } | null>(null)
  const criar = useAcao(
    (ficha?: Ficha) => api.post('/jogadores', { nome: nome.trim(), ficha }),
    [['jogadores'], ['turno']], `${nome.trim()} entrou na mesa.`,
  )
  const gerar = useAcao(() => api.post<{ nome: string; ficha: Ficha }>('/jogadores/gerar', { descricao }))
  const enviar = () => nome.trim() && criar.mutate(undefined, { onSuccess: onFechar })
  const pedirFicha = () => descricao.trim() && gerar.mutate(undefined, {
    onSuccess: (r) => { setNome(r.nome); setGerada((g) => ({ ficha: r.ficha, versao: (g?.versao ?? 0) + 1 })) },
  })

  if (gerada)
    return (
      <DialogAberto onFechar={onFechar}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-4xl">
          <DialogHeader>
            <DialogTitle>Revisar personagem gerado</DialogTitle>
            <DialogDescription>Nada foi gravado ainda. Ajuste o que quiser e clique em “Criar personagem”.</DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="nome-jogador">Nome do jogador (letras, números ou _, sem espaços)</Label>
            <Input id="nome-jogador" value={nome} onChange={(e) => setNome(e.target.value)} />
          </div>
          <FichaForm key={gerada.versao} inicial={gerada.ficha} nome={nome.trim()} onFechar={onFechar}
            rascunho={{
              criando: criar.isPending, bloqueado: !nome.trim(), onVoltar: () => setGerada(null),
              onCriar: (f) => criar.mutate(f, { onSuccess: onFechar }),
            }} />
        </DialogContent>
      </DialogAberto>
    )

  return (
    <DialogAberto onFechar={onFechar}>
      <DialogContent className={modo === 'ia' ? 'max-h-[90vh] overflow-y-auto sm:max-w-2xl' : undefined}>
        <DialogHeader>
          <DialogTitle>Adicionar jogador</DialogTitle>
          <DialogDescription>
            {modo === 'nome'
              ? 'Use letras, números ou _ (sem espaços). O jogador nasce com uma ficha modelo.'
              : 'Descreva o personagem. A IA monta a ficha seguindo as regras, o padrão de status e atributos e o grupo atual; você revisa antes de criar.'}
          </DialogDescription>
        </DialogHeader>
        <div className="flex gap-2">
          <Button size="sm" variant={modo === 'nome' ? 'secondary' : 'outline'} onClick={() => setModo('nome')}>Só o nome</Button>
          <Button size="sm" variant={modo === 'ia' ? 'secondary' : 'outline'} onClick={() => setModo('ia')}>Pedir à IA</Button>
        </div>
        {modo === 'nome' ? (
          <Input autoFocus placeholder="Nome do jogador" value={nome} onChange={(e) => setNome(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && enviar()} />
        ) : (
          <Textarea autoFocus className="max-h-[50vh] min-h-32 overflow-y-auto" value={descricao} disabled={gerar.isPending} onChange={(e) => setDescricao(e.target.value)}
            placeholder="Ex.: policial veterano, cínico, bom de tiro, com medo de altura e uma filha que não vê há anos." />
        )}
        <DialogFooter>
          <Button variant="outline" onClick={onFechar}>Cancelar</Button>
          {modo === 'nome' ? (
            <Button disabled={!nome.trim() || criar.isPending} onClick={enviar}>Adicionar</Button>
          ) : (
            <Button disabled={!descricao.trim() || gerar.isPending} onClick={pedirFicha}>
              {gerar.isPending && <Loader2 className="animate-spin" />}
              {gerar.isPending ? 'Gerando ficha…' : 'Gerar ficha'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </DialogAberto>
  )
}

export function NomeMesaDialog({ iniciar, onFechar }: { iniciar?: boolean; onFechar: () => void }) {
  const { data: atual } = useMesaAtual()
  const [nome, setNome] = useState<string | null>(null)
  const valor = nome ?? atual?.nome ?? ''
  const definir = useAcao(() => api.put('/mesa', { nome: valor }), [['mesa']], 'Nome da mesa salvo.')
  const comecar = useAcaoMestre(() => api.post<AcaoResposta>('/rodada/iniciar'))
  const enviar = () => valor.trim() && definir.mutate(undefined, {
    onSuccess: () => { if (iniciar) comecar.mutate(); onFechar() },
  })
  return (
    <DialogAberto onFechar={onFechar}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Nome da mesa</DialogTitle>
          <DialogDescription>
            {iniciar ? 'Dê um nome à mesa para iniciar a primeira rodada. ' : ''}
            Os backups usam esse nome como prefixo (<b>nome_backup.zip</b>). Use letras, números, espaço, - ou _.
          </DialogDescription>
        </DialogHeader>
        <Input autoFocus placeholder="Nome da mesa" value={valor} onChange={(e) => setNome(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && enviar()} />
        <DialogFooter>
          <Button variant="outline" onClick={onFechar}>Cancelar</Button>
          <Button disabled={!valor.trim() || definir.isPending} onClick={enviar}>{iniciar ? 'Salvar e iniciar rodada' : 'Salvar'}</Button>
        </DialogFooter>
      </DialogContent>
    </DialogAberto>
  )
}

export function ExcluirJogadorDialog({ nome, onFechar }: { nome: string; onFechar: () => void }) {
  const excluir = useAcao(
    () => api.del(`/jogadores/${nome}`),
    [['jogadores'], ['sessao'], ['turno']], `${nome} foi excluído.`,
  )
  return (
    <DialogAberto onFechar={onFechar}>
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
    </DialogAberto>
  )
}

export function CancelarRodadaDialog({ onFechar }: { onFechar: () => void }) {
  const [motivo, setMotivo] = useState('')
  const cancelar = useAcaoMestre(() => api.post<AcaoResposta>('/rodada/cancelar', { motivo }))
  return (
    <DialogAberto onFechar={onFechar}>
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
    </DialogAberto>
  )
}
