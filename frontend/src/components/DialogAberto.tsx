import type { ReactNode } from 'react'
import { Dialog } from '@/components/ui/dialog'

export function DialogAberto({ onFechar, children }: { onFechar: () => void; children: ReactNode }) {
  return <Dialog open onOpenChange={(o) => !o && onFechar()}>{children}</Dialog>
}
