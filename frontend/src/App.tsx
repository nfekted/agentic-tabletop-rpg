import { useMemo, useState } from 'react'
import { AvatarDialog } from '@/features/fichas/AvatarDialog'
import { FichaEditor } from '@/features/fichas/FichaEditor'
import { FichaView } from '@/features/fichas/FichaView'
import { MemoriaDialog } from '@/features/fichas/MemoriaDialog'
import { Mesa } from '@/features/mesa/Mesa'
import { Cabecalho } from '@/features/sistema/Cabecalho'
import { CompressaoWatcher } from '@/features/sistema/CompressaoWatcher'
import { ConfigDialog } from '@/features/sistema/ConfigDialog'
import { CancelarRodadaDialog, ExcluirJogadorDialog, NovoJogadorDialog } from '@/features/sistema/Dialogos'
import { MesasDialog } from '@/features/sistema/MesasDialog'
import { PadraoFichaDialog } from '@/features/sistema/PadraoFichaDialog'
import { RegrasDialog } from '@/features/sistema/RegrasDialog'
import { Sidebar } from '@/features/sistema/Sidebar'
import { TokensView } from '@/features/tokens/TokensView'
import { TurnoView } from '@/features/turno/TurnoView'
import { UiContext, type Modal, type View } from '@/lib/ui-context'

function Modais({ modal, fechar }: { modal: Modal | null; fechar: () => void }) {
  if (!modal) return null
  switch (modal.tipo) {
    case 'ficha-editar': return <FichaEditor nome={modal.nome} onFechar={fechar} />
    case 'ficha-ver': return <FichaView nome={modal.nome} onFechar={fechar} />
    case 'memoria': return <MemoriaDialog nome={modal.nome} onFechar={fechar} />
    case 'avatar': return <AvatarDialog nome={modal.nome} onFechar={fechar} />
    case 'excluir-jogador': return <ExcluirJogadorDialog nome={modal.nome} onFechar={fechar} />
    case 'novo-jogador': return <NovoJogadorDialog onFechar={fechar} />
    case 'regras': return <RegrasDialog onFechar={fechar} />
    case 'padrao-ficha': return <PadraoFichaDialog onFechar={fechar} />
    case 'config': return <ConfigDialog onFechar={fechar} />
    case 'mesas': return <MesasDialog onFechar={fechar} />
    case 'cancelar-rodada': return <CancelarRodadaDialog onFechar={fechar} />
  }
}

export default function App() {
  const [modal, setModal] = useState<Modal | null>(null)
  const [view, setView] = useState<View>('mesa')
  const ctx = useMemo(() => ({ abrir: setModal, fechar: () => setModal(null), view, setView }), [view])

  return (
    <UiContext.Provider value={ctx}>
      <Sidebar />
      <div className="min-h-screen pb-20 md:pb-0 md:pl-16">
        <Cabecalho />
        <main className="mx-auto max-w-[1800px] p-4 md:p-6">
          {view === 'mesa' && <Mesa />}
          {view === 'turnos' && <TurnoView />}
          {view === 'tokens' && <TokensView />}
        </main>
      </div>
      <Modais modal={modal} fechar={ctx.fechar} />
      <CompressaoWatcher />
    </UiContext.Provider>
  )
}
