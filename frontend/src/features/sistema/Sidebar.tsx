import { Dices, ListChecks, Save, ScrollText, Settings, Skull, Swords } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useTurno } from '@/hooks/queries'
import { useUi, type View } from '@/lib/ui-context'
import { cn } from '@/lib/utils'

function Item({ icone: Icone, rotulo, ativo, onClick, ponto }: {
  icone: typeof Dices; rotulo: string; ativo?: boolean; onClick: () => void; ponto?: boolean
}) {
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <button
            onClick={onClick}
            aria-label={rotulo}
            aria-current={ativo ? 'page' : undefined}
            className={cn(
              'relative flex size-11 shrink-0 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-foreground',
              ativo && 'bg-sidebar-accent text-primary',
            )}
          />
        }
      >
        <Icone className="size-5" />
        {ponto && <span className="absolute top-2 right-2 size-2 rounded-full bg-primary" />}
      </TooltipTrigger>
      <TooltipContent side="right" className="hidden md:block">{rotulo}</TooltipContent>
    </Tooltip>
  )
}

// Desktop: barra vertical de ícones. Mobile: barra inferior.
export function Sidebar() {
  const { view, setView, abrir } = useUi()
  const { data: turno } = useTurno()
  const nav = (v: View, icone: typeof Dices, rotulo: string, ponto?: boolean) => (
    <Item icone={icone} rotulo={rotulo} ativo={view === v} onClick={() => setView(v)} ponto={ponto} />
  )
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 flex items-center justify-around border-t bg-sidebar p-1.5 md:inset-y-0 md:right-auto md:w-16 md:flex-col md:justify-start md:gap-1 md:border-t-0 md:border-r md:py-3"
      aria-label="Navegação"
    >
      <div className="hidden size-10 items-center justify-center text-primary md:mb-3 md:flex"><Dices className="size-7" /></div>
      {nav('mesa', Dices, 'Mesa')}
      {nav('turnos', Swords, 'Modo por turnos', turno?.ativo)}
      {nav('tokens', Skull, 'Inimigos, NPCs e itens')}
      <div className="hidden flex-1 md:block" />
      <Item icone={ScrollText} rotulo="Regras" onClick={() => abrir({ tipo: 'regras' })} />
      <Item icone={ListChecks} rotulo="Padrão de status e atributos" onClick={() => abrir({ tipo: 'padrao-ficha' })} />
      <Item icone={Save} rotulo="Salvar / restaurar mesa" onClick={() => abrir({ tipo: 'mesas' })} />
      <Item icone={Settings} rotulo="Configurações da LLM" onClick={() => abrir({ tipo: 'config' })} />
    </nav>
  )
}
