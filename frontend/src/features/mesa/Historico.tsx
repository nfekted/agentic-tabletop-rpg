import { useEffect, useRef } from 'react'
import { Lock, Undo2 } from 'lucide-react'
import { TaggedText } from '@/components/TaggedText'
import { Button } from '@/components/ui/button'
import { filaOcupada, useAcaoMestre, useFila, useSessao } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { AcaoResposta } from '@/lib/types'
import { useUi } from '@/lib/ui-context'
import { cn } from '@/lib/utils'

// linha privada: "@[A|B] Autor: texto" (só A e B a leem no prompt)
const PRIVADA = /^@\[([^\]]*)\] /

export function Historico() {
  const { data: s } = useSessao()
  const { data: fila } = useFila()
  const { setTextoMestre } = useUi()
  const fim = useRef<HTMLDivElement>(null)
  const desfazer = useAcaoMestre(() => api.post<AcaoResposta>('/mestre/desfazer'))
  const linhas = s?.historico ?? []

  // só a última linha: desfazer várias é desfazer uma a uma
  const podeDesfazer = !!s?.pode_desfazer && !filaOcupada(fila) && !desfazer.isPending
  const reverter = () => desfazer.mutate(undefined, { onSuccess: (r) => { if (r.texto) setTextoMestre(r.texto) } })

  useEffect(() => { fim.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) }, [linhas.length])

  return (
    <section className="flex h-full max-h-[32rem] min-h-64 flex-col rounded-2xl border bg-card">
      <h2 className="border-b p-4 font-semibold">🗒️ Histórico da cena atual</h2>
      <div className="flex-1 space-y-2 overflow-y-auto p-4">
        {linhas.length === 0 && <p className="text-sm text-muted-foreground">Nenhum evento ainda nesta rodada.</p>}
        {linhas.map((bruta, i) => {
          const m = PRIVADA.exec(bruta)
          const ouvintes = m ? m[1].split('|') : null
          const linha = m ? bruta.slice(m[0].length) : bruta
          const k = linha.indexOf(':')
          const autor = k >= 0 ? linha.slice(0, k).trim() : 'Mestre'
          const resto = k >= 0 ? linha.slice(k + 1).trim() : linha
          const mestre = autor.startsWith('Mestre')
          return (
            <div key={i} className={cn('flex', mestre ? 'justify-end' : 'justify-start')}>
              <div className={cn('max-w-[85%] rounded-2xl px-3 py-2 text-sm', mestre ? 'bg-primary/15' : 'bg-muted')}>
                <p className="mb-0.5 flex items-center gap-1 text-xs font-semibold text-muted-foreground">
                  {autor}
                  {ouvintes && (
                    <span className="flex items-center gap-0.5 font-normal" title="Só estes jogadores leem esta linha no prompt">
                      <Lock className="size-3" /> {ouvintes.join(', ')}
                    </span>
                  )}
                </p>
                <TaggedText texto={resto} plano={mestre} />
                {podeDesfazer && i === linhas.length - 1 && (
                  <Button variant="ghost" size="xs" className="mt-1 text-muted-foreground" onClick={reverter}
                    title={mestre ? 'Apaga esta fala do histórico e devolve o texto ao campo de envio.' : 'Apaga esta resposta do histórico e da memória da rodada.'}>
                    <Undo2 /> Desfazer
                  </Button>
                )}
              </div>
            </div>
          )
        })}
        <div ref={fim} />
      </div>
    </section>
  )
}
