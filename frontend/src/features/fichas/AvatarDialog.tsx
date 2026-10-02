import { useRef, useState } from 'react'
import { Avatar } from '@/components/Avatar'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useAcao, useJogadores } from '@/hooks/queries'
import { api } from '@/lib/api'

export function AvatarDialog({ nome, onFechar }: { nome: string; onFechar: () => void }) {
  const { data } = useJogadores()
  const j = data?.find((x) => x.nome === nome)
  const [arquivo, setArquivo] = useState<File | null>(null)
  const input = useRef<HTMLInputElement>(null)
  const previa = arquivo ? URL.createObjectURL(arquivo) : null

  const enviar = useAcao(
    () => { const fd = new FormData(); fd.append('arquivo', arquivo!); return api.post(`/jogadores/${nome}/avatar`, fd) },
    [['jogadores']], 'Foto atualizada.',
  )
  const remover = useAcao(() => api.del(`/jogadores/${nome}/avatar`), [['jogadores']], 'Foto removida.')

  return (
    <Dialog open onOpenChange={(o) => !o && onFechar()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Foto de {nome}</DialogTitle>
          <DialogDescription>Aparece no card do jogador e no modo por turnos.</DialogDescription>
        </DialogHeader>
        <div className="flex justify-center">
          {previa
            ? <img src={previa} alt="Prévia" className="size-32 rounded-2xl object-cover ring-1 ring-border" />
            : <Avatar nome={nome} v={j?.avatar_v ?? null} className="size-32 text-2xl" />}
        </div>
        <input ref={input} type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={(e) => setArquivo(e.target.files?.[0] ?? null)} />
        <Button variant="outline" onClick={() => input.current?.click()}>{arquivo ? arquivo.name : 'Escolher imagem…'}</Button>
        <DialogFooter>
          {j?.avatar_v && <Button variant="outline" disabled={remover.isPending} onClick={() => remover.mutate()}>Remover foto</Button>}
          <Button disabled={!arquivo || enviar.isPending} onClick={() => enviar.mutate(undefined, { onSuccess: onFechar })}>Salvar foto</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
