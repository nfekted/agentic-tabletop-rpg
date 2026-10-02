import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAcao, useConfig } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { Config } from '@/lib/types'

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
      provedor: c.provedor, base_url: c.base_url,
      limite_contexto_tokens: c.limite_contexto_tokens,
      gatilho_compressao_pct: c.gatilho_compressao_pct,
      alvo_reducao_pct: c.alvo_reducao_pct,
      api_key: chave ? chave : null, // vazio = manter a chave atual
    }),
    [['config'], ['jogadores']], 'Configurações salvas.',
  )
  const usaChave = c.provedor !== 'Ollama local'
  const usaUrl = c.provedor === 'Ollama local' || c.provedor === 'Omniroute local'
  const num = (k: keyof Config) => (e: React.ChangeEvent<HTMLInputElement>) => setC({ ...c, [k]: Number(e.target.value) })

  return (
    <>
      <Campo id="prov" rotulo="Provedor">
        <Select value={c.provedor} onValueChange={(v) => v && setC({ ...c, provedor: v })}>
          <SelectTrigger id="prov" className="w-full"><SelectValue /></SelectTrigger>
          <SelectContent>
            {c.provedores.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
          </SelectContent>
        </Select>
      </Campo>
      {usaChave && (
        <Campo id="key" rotulo="API Key" dica="Fica salva em arquivos/config.json e nunca é devolvida pela API. Deixe em branco para manter a atual.">
          <Input id="key" type="password" autoComplete="off" value={chave} onChange={(e) => setChave(e.target.value)}
            placeholder={inicial.api_key_definida ? '•••••••• (definida)' : 'Cole sua chave'} />
        </Campo>
      )}
      {usaUrl && (
        <Campo id="url" rotulo="Endereço (base URL)">
          <Input id="url" value={c.base_url} onChange={(e) => setC({ ...c, base_url: e.target.value })} placeholder="http://localhost:8000/v1" />
        </Campo>
      )}
      <div className="grid gap-3 border-t pt-3 sm:grid-cols-3">
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
    <Dialog open onOpenChange={(o) => !o && onFechar()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>⚙️ Configurações da LLM</DialogTitle>
          <DialogDescription>Provedor de modelo e controle de contexto.</DialogDescription>
        </DialogHeader>
        {data ? <Form inicial={data} onFechar={onFechar} /> : <p className="text-sm text-muted-foreground">Carregando…</p>}
      </DialogContent>
    </Dialog>
  )
}
