import { DialogAberto } from '@/components/DialogAberto'
import { DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useFichaMd } from '@/hooks/queries'

export function FichaView({ nome, onFechar }: { nome: string; onFechar: () => void }) {
  const { data } = useFichaMd(nome)
  return (
    <DialogAberto onFechar={onFechar}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader><DialogTitle>👁️ Ficha de {nome}</DialogTitle></DialogHeader>
        <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed">{data?.markdown ?? 'Carregando…'}</pre>
      </DialogContent>
    </DialogAberto>
  )
}
