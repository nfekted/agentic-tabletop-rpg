import { avatarUrl } from '@/lib/api'
import { iniciais } from '@/lib/tags'
import { cn } from '@/lib/utils'

export function Avatar({
  nome, v, className,
}: { nome: string; v: number | null; className?: string }) {
  const url = avatarUrl(nome, v)
  return url ? (
    <img src={url} alt={nome} className={cn('size-12 shrink-0 rounded-xl object-cover ring-1 ring-border', className)} />
  ) : (
    <div
      className={cn(
        'flex size-12 shrink-0 items-center justify-center rounded-xl bg-accent text-sm font-semibold text-accent-foreground ring-1 ring-border',
        className,
      )}
    >
      {iniciais(nome)}
    </div>
  )
}
