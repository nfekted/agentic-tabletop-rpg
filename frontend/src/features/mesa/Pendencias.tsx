import { useState } from 'react'
import { Check, Loader2, X } from 'lucide-react'
import { TaggedText } from '@/components/TaggedText'
import { Button } from '@/components/ui/button'
import { useAcaoMestre, useSessao } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { AcaoResposta, Tags } from '@/lib/types'
import { cn } from '@/lib/utils'

function Resposta({ tags, publico }: { tags: Tags; publico: string }) {
  return (
    <div className="space-y-1.5 text-sm">
      {tags.pensamento && (
        <p className="rounded-lg bg-violet-500/10 p-2 text-violet-200 italic">
          💭 <b>Pensamento íntimo (privado):</b> {tags.pensamento}
        </p>
      )}
      <TaggedText texto={publico} />
    </div>
  )
}

export function Pendencias() {
  const { data: s } = useSessao()
  const [destinos, setDestinos] = useState<string[]>([])

  const post = (url: string) => api.post<AcaoResposta>(url)
  const aprovar = useAcaoMestre(() => post('/pendencias/principal/aprovar'))
  const descartar = useAcaoMestre(() => post('/pendencias/principal/descartar'))
  const gerar = useAcaoMestre(() => api.post<AcaoResposta>('/pendencias/redirect/gerar', { destinos }))
  const ignorar = useAcaoMestre(() => post('/pendencias/redirect/ignorar'))
  const aprovarR = useAcaoMestre((id: string) => post(`/pendencias/redirect/${id}/aprovar`))
  const descartarR = useAcaoMestre((id: string) => post(`/pendencias/redirect/${id}/descartar`))

  if (!s) return null
  const p = s.pending_principal
  const ar = s.aguardando_redirect
  const reds = s.pending_redirects
  if (!p && !ar && !reds.length) return null

  return (
    <div className="space-y-3">
      {p && (
        <section className="space-y-3 rounded-2xl border border-dashed border-amber-400/60 bg-amber-400/5 p-4">
          <h2 className="font-semibold">🤖 Retorno de {p.alvo}</h2>
          <Resposta tags={p.tags} publico={p.conteudo_publico} />
          <div className="flex gap-2">
            <Button disabled={aprovar.isPending || descartar.isPending} onClick={() => aprovar.mutate()}>
              {aprovar.isPending ? <Loader2 className="animate-spin" /> : <Check />} Aprovar / Espelhar
            </Button>
            <Button variant="outline" disabled={aprovar.isPending || descartar.isPending} onClick={() => descartar.mutate()}>
              <X /> Descartar
            </Button>
          </div>
        </section>
      )}

      {ar && (
        <section className="space-y-3 rounded-2xl border border-sky-400/50 bg-sky-400/5 p-4">
          <h2 className="font-semibold">❓ {ar.alvo_principal} fez uma pergunta</h2>
          <blockquote className="border-l-2 border-sky-400/60 pl-3 text-sm">{ar.resposta_pergunta}</blockquote>
          <p className="text-sm text-muted-foreground">Para quem deseja redirecionar essa dúvida?</p>
          <div className="flex flex-wrap gap-1.5">
            {ar.candidatos.map((c) => (
              <button
                key={c}
                onClick={() => setDestinos((d) => (d.includes(c) ? d.filter((x) => x !== c) : [...d, c]))}
                className={cn(
                  'rounded-lg border px-2.5 py-1 text-sm',
                  destinos.includes(c) ? 'border-primary bg-primary/15 text-primary' : 'hover:bg-muted',
                )}
              >
                {c}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <Button
              disabled={!destinos.length || gerar.isPending}
              onClick={() => gerar.mutate(undefined, { onSuccess: () => setDestinos([]) })}
            >
              {gerar.isPending && <Loader2 className="animate-spin" />} Gerar resposta(s)
            </Button>
            <Button variant="outline" disabled={gerar.isPending} onClick={() => ignorar.mutate()}>
              Não redirecionar
            </Button>
          </div>
        </section>
      )}

      {reds.length > 0 && (
        <section className="space-y-3 rounded-2xl border border-dashed border-amber-400/60 bg-amber-400/5 p-4">
          <h2 className="font-semibold">🤖 Respostas às dúvidas redirecionadas</h2>
          {reds.map((r) => (
            <div key={r.id} className="space-y-2 border-t pt-3 first:border-0 first:pt-0">
              <p className="text-sm font-medium">
                {r.destino} <span className="font-normal text-muted-foreground">(resposta a {r.alvo_principal})</span>
              </p>
              <Resposta tags={r.tags} publico={r.conteudo_publico} />
              <div className="flex gap-2">
                <Button size="sm" onClick={() => aprovarR.mutate(r.id)} disabled={aprovarR.isPending || descartarR.isPending}>
                  <Check /> Aprovar
                </Button>
                <Button size="sm" variant="outline" onClick={() => descartarR.mutate(r.id)} disabled={aprovarR.isPending || descartarR.isPending}>
                  <X /> Descartar
                </Button>
              </div>
            </div>
          ))}
        </section>
      )}
    </div>
  )
}
