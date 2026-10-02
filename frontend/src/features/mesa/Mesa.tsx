import { Plus } from 'lucide-react'
import { useJogadores, useSessao } from '@/hooks/queries'
import { useUi } from '@/lib/ui-context'
import { AcaoMestre } from './AcaoMestre'
import { Historico } from './Historico'
import { JogadorCard } from './JogadorCard'
import { Pendencias } from './Pendencias'

export function Mesa() {
  const { data: jogadores = [], isLoading } = useJogadores()
  const { data: sessao } = useSessao()
  const { abrir } = useUi()

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
        {jogadores.map((j) => (
          <JogadorCard key={j.nome} jogador={j} fala={sessao?.ultima_fala[j.nome]} />
        ))}
        <button
          onClick={() => abrir({ tipo: 'novo-jogador' })}
          className="flex min-h-32 flex-col items-center justify-center gap-1 rounded-2xl border border-dashed text-muted-foreground transition-colors hover:border-primary hover:text-primary"
        >
          <Plus className="size-6" />
          <span className="text-sm">{isLoading ? 'Carregando…' : jogadores.length ? 'Adicionar jogador' : 'Adicione o primeiro jogador'}</span>
        </button>
      </div>

      <Pendencias />

      <div className="grid gap-6 lg:grid-cols-2">
        <AcaoMestre />
        <Historico />
      </div>
    </div>
  )
}
