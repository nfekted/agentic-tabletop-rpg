import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAcao, useFicha, usePadraoFicha } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { Ficha } from '@/lib/types'
import { CamposFixos, type Campo } from './CamposFixos'
import { HabilidadesEditor } from './HabilidadesEditor'
import { ItensEditor } from './ItensEditor'
import { ListaNomeValor } from './ListaNomeValor'
import { AtributosValores, AvisoSemPadrao, StatusValores } from './ValoresPadrao'

const CAMPOS_BASE: Campo[] = [
  { chave: 'nome', rotulo: 'Nome', dica: 'Nome do personagem' },
  { chave: 'classe', rotulo: 'Classe', dica: 'Ex.: Guerreiro, Mago, Ladino' },
  { chave: 'passado_origem', rotulo: 'Passado/Origem', dica: 'Uma frase sobre quem ele é e sua motivação' },
]
const CAMPOS_PERSONALIDADE: Campo[] = [
  { chave: 'tratamento_personalidade', rotulo: 'Tratamento/Personalidade', dica: 'Como interage com os outros. Ex.: tímido, mas valente' },
  { chave: 'medos_gatilhos', rotulo: 'Medos/Gatilhos', dica: 'Fobias, traumas, o que tira o personagem do sério' },
  { chave: 'segredos_pessoais', rotulo: 'Segredos pessoais', dica: 'Informações confidenciais de background' },
]

function Form({ inicial, nome, onFechar }: { inicial: Ficha; nome: string; onFechar: () => void }) {
  const [f, setF] = useState<Ficha>(inicial)
  const { data: padrao } = usePadraoFicha()
  const semPadrao = padrao && !padrao.configurado
  const salvar = useAcao(
    () => api.put<Ficha>(`/fichas/${nome}`, f),
    [['jogadores'], ['ficha', nome], ['ficha-md', nome]],
    'Ficha salva.',
  )
  const salvarEFechar = () => salvar.mutate(undefined, { onSuccess: onFechar })

  return (
    <>
      <div className="space-y-1.5">
        <Label htmlFor="mods">Modificadores (separados por vírgula)</Label>
        <Input id="mods" value={f.modificadores} onChange={(e) => setF({ ...f, modificadores: e.target.value })} placeholder="Envenenado, +2 Força" />
      </div>
      <Tabs defaultValue="base">
        <TabsList className="flex-wrap">
          <TabsTrigger value="base">Base</TabsTrigger>
          <TabsTrigger value="status">Status</TabsTrigger>
          <TabsTrigger value="geral">Atributos e perícias</TabsTrigger>
          <TabsTrigger value="habilidades">Habilidades</TabsTrigger>
          <TabsTrigger value="itens">Itens</TabsTrigger>
          <TabsTrigger value="personalidade">Personalidade</TabsTrigger>
        </TabsList>
        <TabsContent value="base" className="pt-2">
          <CamposFixos campos={CAMPOS_BASE} valores={f.base} onChange={(v) => setF({ ...f, base: v as Ficha['base'] })} />
        </TabsContent>
        <TabsContent value="status" className="pt-2">
          {semPadrao ? <AvisoSemPadrao /> : <StatusValores status={f.status} onChange={(status) => setF({ ...f, status })} />}
        </TabsContent>
        <TabsContent value="geral" className="grid gap-3 pt-2 md:grid-cols-2">
          {semPadrao
            ? <AvisoSemPadrao />
            : <AtributosValores atributos={f.atributos} onChange={(atributos) => setF({ ...f, atributos })} />}
          <ListaNomeValor titulo="Perícias" itens={f.pericias} rotuloAdicionar="Perícia" exemploNome="Espada" exemploValor="Treinado"
            onChange={(pericias) => setF({ ...f, pericias })} />
        </TabsContent>
        <TabsContent value="habilidades" className="pt-2">
          <HabilidadesEditor valor={f.habilidades} onChange={(habilidades) => setF({ ...f, habilidades })} />
        </TabsContent>
        <TabsContent value="itens" className="pt-2">
          <ItensEditor valor={f.itens} onChange={(itens) => setF({ ...f, itens })} />
        </TabsContent>
        <TabsContent value="personalidade" className="pt-2">
          <CamposFixos multilinha campos={CAMPOS_PERSONALIDADE} valores={f.personalidade}
            onChange={(v) => setF({ ...f, personalidade: v as Ficha['personalidade'] })} />
        </TabsContent>
      </Tabs>
      <DialogFooter>
        <Button variant="outline" onClick={onFechar}>Cancelar</Button>
        <Button disabled={salvar.isPending} onClick={salvarEFechar}>Salvar ficha</Button>
      </DialogFooter>
    </>
  )
}

export function FichaEditor({ nome, onFechar }: { nome: string; onFechar: () => void }) {
  const { data, isLoading } = useFicha(nome)
  return (
    <Dialog open onOpenChange={(o) => !o && onFechar()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>Ficha de {nome}</DialogTitle>
          <DialogDescription>Preencha os campos; o que ficar em branco não vai para o prompt do agente.</DialogDescription>
        </DialogHeader>
        {isLoading || !data ? <p className="text-sm text-muted-foreground">Carregando…</p> : <Form inicial={data} nome={nome} onFechar={onFechar} />}
      </DialogContent>
    </Dialog>
  )
}
