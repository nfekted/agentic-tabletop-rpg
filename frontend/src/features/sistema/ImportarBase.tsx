import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAcao, useMesasSalvas } from '@/hooks/queries'
import { api } from '@/lib/api'

const PARTES = [
  { id: 'personagens', rotulo: 'Personagens', dica: 'só os vivos: ficha e foto (memória começa vazia)' },
  { id: 'regras', rotulo: 'Regras definidas', dica: 'todos os conjuntos e o ativo' },
  { id: 'padrao', rotulo: 'Padrão de status e atributos', dica: '' },
  { id: 'anotacoes', rotulo: 'Anotações do mestre', dica: '' },
  { id: 'inimigos', rotulo: 'Inimigos', dica: '' },
  { id: 'npcs', rotulo: 'NPCs', dica: '' },
  { id: 'itens', rotulo: 'Itens', dica: '' },
]

// Cria uma mesa NOVA a partir de um backup: apaga a mesa atual e traz só as partes marcadas (nada é mesclado).
export function ImportarBase({ onCancelar, onFeito }: { onCancelar: () => void; onFeito: () => void }) {
  const qc = useQueryClient()
  const { data: mesas = [] } = useMesasSalvas()
  const [backup, setBackup] = useState('')
  const [partes, setPartes] = useState<string[]>(PARTES.map((p) => p.id))
  const [nome, setNome] = useState('')

  const importar = useAcao(
    () => api.post<{ mensagem: string }>('/mesas/importar-base', { backup, categorias: partes, nome: nome.trim() }),
    [], (r) => r.mensagem,
  )
  const alternar = (id: string) => setPartes((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]))
  const pronto = !!backup && partes.length > 0 && !!nome.trim() && !importar.isPending

  return (
    <div className="space-y-3 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm">
      <p>
        Começa uma <b>mesa nova</b> usando um backup só como base. Tudo o que está na mesa atual é <b>apagado</b>
        (não dá para recuperar; recomendamos salvar um backup antes) e entra apenas o que for marcado abaixo.
        Cenas, memórias, rodadas e combate não são trazidos.
      </p>
      <select value={backup} onChange={(e) => setBackup(e.target.value)} aria-label="Backup de origem"
        className="h-8 w-full rounded-lg border bg-background px-2 text-sm">
        <option value="">Escolha o backup de origem…</option>
        {mesas.map((m) => <option key={m.nome} value={m.nome}>{m.nome}{m.autosave ? ' (autosave)' : ''}</option>)}
      </select>
      <div className="grid gap-1 sm:grid-cols-2">
        {PARTES.map((p) => (
          <label key={p.id} className="flex items-start gap-2">
            <input type="checkbox" className="mt-1" checked={partes.includes(p.id)} onChange={() => alternar(p.id)} />
            <span>
              {p.rotulo}
              {p.dica && <span className="block text-xs text-muted-foreground">{p.dica}</span>}
            </span>
          </label>
        ))}
      </div>
      <Input placeholder="Nome da nova mesa" value={nome} onChange={(e) => setNome(e.target.value)} />
      <div className="flex gap-2">
        <Button variant="destructive" size="sm" disabled={!pronto}
          onClick={() => importar.mutate(undefined, { onSuccess: () => { qc.invalidateQueries(); onFeito() } })}>
          Sim, criar nova mesa
        </Button>
        <Button variant="outline" size="sm" onClick={onCancelar}>Não</Button>
      </div>
    </div>
  )
}
