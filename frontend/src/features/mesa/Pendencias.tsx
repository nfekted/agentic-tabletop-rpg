import { Check, Loader2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAcaoMestre, useSessao } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { AcaoResposta } from '@/lib/types'

// Um personagem quis acionar outro jogador: a fala dele já foi registrada; o mestre decide se o chamado entra.
export function Pendencias() {
  const { data: s } = useSessao()
  const post = (url: string) => api.post<AcaoResposta>(url)
  const aprovar = useAcaoMestre((id: string) => post(`/pendencias/chamada/${id}/aprovar`))
  const descartar = useAcaoMestre((id: string) => post(`/pendencias/chamada/${id}/descartar`))

  const chamadas = s?.pending_chamadas ?? []
  if (!chamadas.length) return null
  const ocupado = aprovar.isPending || descartar.isPending

  return (
    <section className="space-y-3 rounded-2xl border border-dashed border-amber-400/60 bg-amber-400/5 p-4">
      <h2 className="font-semibold">📣 Chamadas aguardando você</h2>
      {chamadas.map((c) => (
        <div key={c.id} className="space-y-2 border-t pt-3 first:border-0 first:pt-0">
          <p className="text-sm">
            <b>{c.origem}</b> chama <b>{c.destino}</b>:
          </p>
          <blockquote className="border-l-2 border-amber-400/60 pl-3 text-sm">{c.mensagem}</blockquote>
          {!c.presentes.includes(c.destino) && (
            <p className="text-xs text-muted-foreground">{c.destino} não está nesta cena: acionar o inclui nela.</p>
          )}
          <div className="flex gap-2">
            <Button size="sm" disabled={ocupado} onClick={() => aprovar.mutate(c.id)}>
              {aprovar.isPending ? <Loader2 className="animate-spin" /> : <Check />} Acionar {c.destino}
            </Button>
            <Button size="sm" variant="outline" disabled={ocupado} onClick={() => descartar.mutate(c.id)}>
              <X /> Não acionar
            </Button>
          </div>
        </div>
      ))}
    </section>
  )
}
