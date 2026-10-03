import { useEffect, useRef } from 'react'
import { TaggedText } from '@/components/TaggedText'
import { useSessao } from '@/hooks/queries'
import { cn } from '@/lib/utils'

export function Historico() {
  const { data: s } = useSessao()
  const fim = useRef<HTMLDivElement>(null)
  const linhas = s?.historico ?? []

  useEffect(() => { fim.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) }, [linhas.length])

  return (
    <section className="flex h-full max-h-[32rem] min-h-64 flex-col rounded-2xl border bg-card">
      <h2 className="border-b p-4 font-semibold">🗒️ Histórico da cena atual</h2>
      <div className="flex-1 space-y-2 overflow-y-auto p-4">
        {linhas.length === 0 && <p className="text-sm text-muted-foreground">Nenhum evento ainda nesta rodada.</p>}
        {linhas.map((linha, i) => {
          const k = linha.indexOf(':')
          const autor = k >= 0 ? linha.slice(0, k).trim() : 'Mestre'
          const resto = k >= 0 ? linha.slice(k + 1).trim() : linha
          const mestre = autor.startsWith('Mestre')
          return (
            <div key={i} className={cn('flex', mestre ? 'justify-end' : 'justify-start')}>
              <div className={cn('max-w-[85%] rounded-2xl px-3 py-2 text-sm', mestre ? 'bg-primary/15' : 'bg-muted')}>
                <p className="mb-0.5 text-xs font-semibold text-muted-foreground">{autor}</p>
                <TaggedText texto={resto} plano={mestre} />
              </div>
            </div>
          )
        })}
        <div ref={fim} />
      </div>
    </section>
  )
}
