import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useMemoria } from '@/hooks/queries'

function Texto({ children }: { children: string }) {
  return (
    <pre className="max-h-[55vh] overflow-y-auto whitespace-pre-wrap break-words rounded-lg bg-muted/50 p-3 font-sans text-sm">
      {children || '(vazio)'}
    </pre>
  )
}

function Lista({ itens }: { itens: { arquivo: string; conteudo: string }[] }) {
  if (!itens.length) return <p className="text-sm text-muted-foreground">Nada aqui ainda.</p>
  return (
    <div className="max-h-[55vh] space-y-3 overflow-y-auto">
      {itens.map((i) => (
        <div key={i.arquivo}>
          <p className="mb-1 text-xs font-semibold text-muted-foreground">{i.arquivo}</p>
          <Texto>{i.conteudo}</Texto>
        </div>
      ))}
    </div>
  )
}

export function MemoriaDialog({ nome, onFechar }: { nome: string; onFechar: () => void }) {
  const { data: m } = useMemoria(nome)
  return (
    <Dialog open onOpenChange={(o) => !o && onFechar()}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader><DialogTitle>📖 Memória de {nome}</DialogTitle></DialogHeader>
        {!m ? <p className="text-sm text-muted-foreground">Carregando…</p> : (
          <Tabs defaultValue="mesa">
            <TabsList>
              <TabsTrigger value="mesa">Mesa</TabsTrigger>
              <TabsTrigger value="cenas">Cenas ({m.cenas.length})</TabsTrigger>
              <TabsTrigger value="rodadas">Rodadas ({m.rodadas.length})</TabsTrigger>
              <TabsTrigger value="atual">Rodada atual</TabsTrigger>
            </TabsList>
            <TabsContent value="mesa"><Texto>{m.mesa}</Texto></TabsContent>
            <TabsContent value="cenas"><Lista itens={m.cenas} /></TabsContent>
            <TabsContent value="rodadas"><Lista itens={m.rodadas} /></TabsContent>
            <TabsContent value="atual"><Texto>{m.rodada_atual}</Texto></TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  )
}
