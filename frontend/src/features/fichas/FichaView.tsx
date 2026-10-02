import { useQuery } from '@tanstack/react-query'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { api } from '@/lib/api'

export function FichaView({ nome, onFechar }: { nome: string; onFechar: () => void }) {
  const { data } = useQuery({
    queryKey: ['ficha-md', nome],
    queryFn: () => api.get<{ markdown: string }>(`/fichas/${nome}/consolidada`),
    gcTime: 0,
  })
  return (
    <Dialog open onOpenChange={(o) => !o && onFechar()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader><DialogTitle>👁️ Ficha de {nome}</DialogTitle></DialogHeader>
        <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed">{data?.markdown ?? 'Carregando…'}</pre>
      </DialogContent>
    </Dialog>
  )
}
