// MODO TESTE: para remover, apague este arquivo e as marcações MODO-TESTE (ver rpg/modo_teste.py).
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { useAcao, useModoTeste } from '@/hooks/queries'
import { api } from '@/lib/api'

export function ModoTeste() {
  const { data } = useModoTeste()
  const alternar = useAcao((ativo: boolean) => api.put('/modo-teste', { ativo }), [['modo-teste']])
  const ativo = !!data?.ativo
  return (
    <label
      className="flex items-center gap-1.5 text-sm"
      title="Respostas simuladas e memória sem resumo: nenhuma chamada à IA."
    >
      <Switch size="sm" checked={ativo} disabled={alternar.isPending} onCheckedChange={(v) => alternar.mutate(v)} />
      Modo testes
      {ativo && <Badge variant="outline">TESTE</Badge>}
    </label>
  )
}
