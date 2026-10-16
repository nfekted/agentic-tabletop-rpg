import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Loader2, PlugZap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DialogAberto } from '@/components/DialogAberto'
import {
  DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAcao, useConfig } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { Config } from '@/lib/types'
import { cn } from '@/lib/utils'
import { Carregando } from '@/components/Carregando'

function Campo({ id, rotulo, dica, children }: { id: string; rotulo: string; dica?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <Label htmlFor={id}>{rotulo}</Label>
      {children}
      {dica && <p className="text-xs text-muted-foreground">{dica}</p>}
    </div>
  )
}

function Form({ inicial, onFechar }: { inicial: Config; onFechar: () => void }) {
  const [c, setC] = useState(inicial)
  const [chave, setChave] = useState('')
  const salvar = useAcao(
    () => api.put<Config>('/config', {
      tipo_api: c.tipo_api, modelo: c.modelo, base_url: c.base_url,
      limite_contexto_tokens: c.limite_contexto_tokens,
      gatilho_compressao_pct: c.gatilho_compressao_pct,
      alvo_reducao_pct: c.alvo_reducao_pct,
      limite_rpm: c.limite_rpm, limite_tpm: c.limite_tpm, limite_rpd: c.limite_rpd,
      fila_sempre_visivel: c.fila_sempre_visivel,
      api_key: chave ? chave : null, // vazio = manter a chave atual
    }),
    [['config'], ['jogadores'], ['limites']], 'Configurações salvas.',
  )
  const [teste, setTeste] = useState<{ ok: boolean; mensagem: string } | null>(null)
  const testar = useMutation({
    mutationFn: () => api.post<{ ok: boolean; mensagem: string }>('/config/testar', {
      tipo_api: c.tipo_api, modelo: c.modelo, base_url: c.base_url, api_key: chave ? chave : null,
    }),
    onMutate: () => setTeste(null),
    onSuccess: setTeste,
    onError: (e: Error) => setTeste({ ok: false, mensagem: e.message }),
  })
  const usaUrl = c.tipo_api !== 'gemini'
  const num = (k: keyof Config) => (e: React.ChangeEvent<HTMLInputElement>) => setC({ ...c, [k]: Number(e.target.value) })

  return (
    <>
      <Tabs defaultValue="modelo">
        <TabsList variant="line" className="w-full justify-start border-b">
          <TabsTrigger value="modelo" className="flex-none px-3">Modelo</TabsTrigger>
          <TabsTrigger value="limites" className="flex-none px-3">Limites</TabsTrigger>
          <TabsTrigger value="interface" className="flex-none px-3">Interface</TabsTrigger>
        </TabsList>

        <div className="min-h-80 pt-3">
          <TabsContent value="modelo" className="space-y-3">
            <Campo id="prov" rotulo="Tipo de API" dica="Qual protocolo usar. DeepSeek, Kimi, Groq, OpenRouter etc. usam OpenAI-compatível.">
              <Select value={c.tipo_api} onValueChange={(v) => v && setC({ ...c, tipo_api: v })}>
                <SelectTrigger id="prov" className="w-full">
                  <SelectValue>{(v: string) => c.tipos_api.find((t) => t.id === v)?.nome ?? v}</SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {c.tipos_api.map((t) => <SelectItem key={t.id} value={t.id}>{t.nome}</SelectItem>)}
                </SelectContent>
              </Select>
            </Campo>
            <Campo id="modelo" rotulo="Modelo" dica="Nome exatamente como na documentação do provedor (ex.: gemini-3.5-flash-lite).">
              <Input id="modelo" value={c.modelo} onChange={(e) => setC({ ...c, modelo: e.target.value })} placeholder="nome-do-modelo" />
            </Campo>
            {usaUrl && (
              <Campo id="url" rotulo="Endereço (base URL)"
                dica={c.tipo_api === 'openai' ? 'Vazio = API oficial da OpenAI.' : 'Ollama: http://localhost:11434/v1 · Omniroute: http://localhost:8000/v1'}>
                <Input id="url" value={c.base_url} onChange={(e) => setC({ ...c, base_url: e.target.value })} placeholder="http://localhost:8000/v1" />
              </Campo>
            )}
            <Campo id="key" rotulo="API Key" dica="Fica salva em arquivos/config.json e nunca é devolvida pela API. Deixe em branco para manter a atual (em servidor local costuma não ser necessária).">
              <Input id="key" type="password" autoComplete="off" value={chave} onChange={(e) => setChave(e.target.value)}
                placeholder={inicial.api_key_definida ? '•••••••• (definida)' : 'Cole sua chave'} />
            </Campo>
            <div className="space-y-2 border-t pt-3">
              <Button variant="secondary" size="sm" disabled={testar.isPending || !c.modelo.trim()} onClick={() => testar.mutate()}>
                {testar.isPending ? <Loader2 className="animate-spin" /> : <PlugZap />} Testar conexão
              </Button>
              {testar.isPending && <p className="text-xs text-muted-foreground">Testando... o primeiro request a um modelo local pode demorar (carregando o modelo).</p>}
              {teste && <p className={cn('break-words text-xs', teste.ok ? 'text-emerald-500' : 'text-destructive')}>{teste.mensagem}</p>}
              <p className="text-xs text-muted-foreground">Usa os valores desta tela, mesmo sem salvar. Não conta nos limites.</p>
            </div>
          </TabsContent>

          <TabsContent value="limites" className="space-y-4">
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Limites do provedor</p>
              <div className="grid gap-3 sm:grid-cols-3">
                <Campo id="rpm" rotulo="RPM" dica="Requisições por minuto. 0 = sem controle.">
                  <Input id="rpm" type="number" min={0} value={c.limite_rpm} onChange={num('limite_rpm')} />
                </Campo>
                <Campo id="tpm" rotulo="TPM" dica="Tokens por minuto. 0 = sem controle.">
                  <Input id="tpm" type="number" min={0} value={c.limite_tpm} onChange={num('limite_tpm')} />
                </Campo>
                <Campo id="rpd" rotulo="RPD" dica="Requisições por dia. 0 = sem controle.">
                  <Input id="rpd" type="number" min={0} value={c.limite_rpd} onChange={num('limite_rpd')} />
                </Campo>
              </div>
            </div>
            <div className="border-t pt-3">
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Contexto e compressão</p>
              <div className="grid gap-3 sm:grid-cols-3">
                <Campo id="lim" rotulo="Contexto máx. (tokens)" dica="Limite da LLM. 0 desliga o controle.">
                  <Input id="lim" type="number" min={0} value={c.limite_contexto_tokens} onChange={num('limite_contexto_tokens')} />
                </Campo>
                <Campo id="gat" rotulo="Gatilho (%)" dica="Ocupação que oferece a compressão.">
                  <Input id="gat" type="number" min={1} max={100} value={c.gatilho_compressao_pct} onChange={num('gatilho_compressao_pct')} />
                </Campo>
                <Campo id="alvo" rotulo="Redução alvo (%)" dica="Quanto do mesa.txt é cortado.">
                  <Input id="alvo" type="number" min={1} max={95} value={c.alvo_reducao_pct} onChange={num('alvo_reducao_pct')} />
                </Campo>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="interface" className="space-y-3">
            <div className="flex items-start justify-between gap-4 rounded-lg border p-3">
              <Label htmlFor="fila-sempre" className="flex-col items-start gap-0.5">
                <span>Sempre exibir fila de ações</span>
                <span className="text-xs font-normal text-muted-foreground">
                  Mostra os passos de cada jogador mesmo com RPM/TPM desligados. Útil em modelos locais para acompanhar as respostas.
                </span>
              </Label>
              <Switch id="fila-sempre" checked={c.fila_sempre_visivel} onCheckedChange={(v) => setC({ ...c, fila_sempre_visivel: v })} />
            </div>
          </TabsContent>

        </div>
      </Tabs>
      <DialogFooter>
        <Button variant="outline" onClick={onFechar}>Cancelar</Button>
        <Button disabled={salvar.isPending} onClick={() => salvar.mutate(undefined, { onSuccess: onFechar })}>Salvar</Button>
      </DialogFooter>
    </>
  )
}

export function ConfigDialog({ onFechar }: { onFechar: () => void }) {
  const { data } = useConfig()
  return (
    <DialogAberto onFechar={onFechar}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>⚙️ Configurações</DialogTitle>
          <DialogDescription>Modelo, limites e interface.</DialogDescription>
        </DialogHeader>
        {data ? <Form inicial={data} onFechar={onFechar} /> : <Carregando />}
      </DialogContent>
    </DialogAberto>
  )
}
