import { useState } from 'react'
import { MessageSquare, X } from 'lucide-react'
import { TaggedText } from '@/components/TaggedText'
import type { Fala } from '@/lib/types'
import { cn } from '@/lib/utils'

// Balão da última fala: cinza = aprovada, âmbar tracejado = aguardando aprovação, roxo = pensamento privado.
export function Balao({ fala, compacto }: { fala?: Fala; compacto?: boolean }) {
  const [fechada, setFechada] = useState<number | null>(null)
  if (!fala) return null

  if (fechada === fala.seq)
    return (
      <button
        onClick={() => setFechada(null)}
        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
      >
        <MessageSquare className="size-3" /> Restaurar última fala
      </button>
    )

  const estilo = fala.privado
    ? 'border-violet-500/60 bg-violet-500/10 italic'
    : fala.aprovada
      ? 'border-border bg-muted/60'
      : 'border-dashed border-amber-400/70 bg-amber-400/10'

  return (
    <div>
      <div
        className={cn(
          'relative max-h-48 overflow-y-auto rounded-xl border px-2.5 py-2 pr-6 text-[13px] leading-snug',
          compacto && 'max-h-32 text-xs',
          estilo,
        )}
      >
        <button
          onClick={() => setFechada(fala.seq)}
          className="absolute top-1 right-1 rounded p-0.5 text-muted-foreground hover:text-foreground"
          aria-label="Fechar fala"
        >
          <X className="size-3" />
        </button>
        <TaggedText texto={fala.texto} />
      </div>
      {fala.privado && <p className="mt-0.5 text-[11px] text-violet-300">💭 pensamento privado — só o mestre vê</p>}
      {!fala.privado && !fala.aprovada && (
        <p className="mt-0.5 text-[11px] text-amber-300">⏳ aguardando aprovação do mestre</p>
      )}
    </div>
  )
}
