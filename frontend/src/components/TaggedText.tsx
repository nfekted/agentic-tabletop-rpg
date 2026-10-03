import { Brain } from 'lucide-react'
import { parseTags } from '@/lib/tags'
import { cn } from '@/lib/utils'

// Renderiza uma resposta de agente com as tags ([fala], [acao]...) já formatadas.
export function TaggedText({ texto, className, plano }: { texto: string; className?: string; plano?: boolean }) {
  if (plano) return <span className={cn('whitespace-pre-wrap break-words', className)}>{texto}</span>
  const segs = parseTags(texto)
  return (
    <span className={cn('whitespace-pre-wrap break-words', className)}>
      {segs.map((s, i) => {
        if (s.tipo === 'pensamento')
          return (
            <em key={i} className="flex items-start gap-1.5 text-[#a0aec0]">
              <Brain className="mt-0.5 size-3.5 shrink-0" aria-label="Pensamento" /> <span>{s.texto}</span>
            </em>
          )
        if (s.tipo === 'acao') return <em key={i} className="block text-amber-200/90">⚔️ {s.texto}</em>
        if (s.tipo === 'duvida') return <span key={i} className="block text-sky-300">❓ {s.texto}</span>
        return <span key={i} className="block">“{s.texto}”</span>
      })}
    </span>
  )
}
