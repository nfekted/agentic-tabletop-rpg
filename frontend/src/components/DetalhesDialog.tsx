import { DialogAberto } from '@/components/DialogAberto'
import { Carregando } from '@/components/Carregando'
import { DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useFicha } from '@/hooks/queries'
import { acharDetalhes } from '@/lib/detalhes'

// Mostra, direto da ficha, os dados das habilidades, poderes, passivas e itens citados na fala.
export function DetalhesDialog({ nome, texto, onFechar }: { nome: string; texto: string; onFechar: () => void }) {
  const { data } = useFicha(nome)
  const achados = data ? acharDetalhes(data, texto) : []
  return (
    <DialogAberto onFechar={onFechar}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>ℹ️ Detalhes citados por {nome}</DialogTitle>
          <DialogDescription>Habilidades, poderes, passivas e itens (equipados ou na mochila) mencionados nesta fala.</DialogDescription>
        </DialogHeader>
        {!data ? <Carregando /> : achados.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nenhuma habilidade, poder, passiva ou item da ficha foi identificado nesta fala.</p>
        ) : achados.map((d) => (
          <section key={`${d.tipo}:${d.nome}`} className="space-y-1 rounded-lg border p-3">
            <h3 className="text-sm font-semibold">{d.nome} <span className="text-xs font-normal text-muted-foreground">· {d.tipo}</span></h3>
            <p className="whitespace-pre-wrap text-sm">{d.texto || 'Sem detalhes preenchidos na ficha.'}</p>
          </section>
        ))}
      </DialogContent>
    </DialogAberto>
  )
}
