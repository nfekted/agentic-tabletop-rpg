import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { usePensando } from '@/hooks/eventos'
import { useAcao, useSessao } from '@/hooks/queries'
import { api } from '@/lib/api'

type Pergunta = { agente: string; memoria_util: boolean }

// Oferece a compressão de memória (diálogo em roleplay) quando o contexto de um personagem passa do gatilho.
export function CompressaoWatcher() {
  const { dataUpdatedAt } = useSessao()
  const pensando = usePensando()
  const [fila, setFila] = useState<Pergunta[]>([])

  useEffect(() => {
    if (pensando.size > 0) return
    const t = setTimeout(async () => {
      try {
        const p = await api.get<Pergunta | null>('/compressao/pendente')
        if (p) setFila((f) => (f.some((x) => x.agente === p.agente) ? f : [...f, p]))
      } catch { /* API fora do ar: o aviso aparece em outros pontos */ }
    }, 1200)
    return () => clearTimeout(t)
  }, [dataUpdatedAt, pensando.size])

  const atual = fila[0]
  const proximo = () => setFila((f) => f.slice(1))
  const comprimir = useAcao(
    (nome: string) => api.post<{ ok: boolean; mensagem: string }>(`/memoria/${nome}/comprimir`),
    [['jogadores']],
  )

  if (!atual) return null
  const nome = atual.agente
  return (
    <Dialog open onOpenChange={(o) => !o && !comprimir.isPending && proximo()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>🧠 Mente sobrecarregada</DialogTitle>
          <DialogDescription>
            {atual.memoria_util
              ? `${nome} está com muitas coisas na cabeça... a concentração cai, detalhes são esquecidos, regras deixam de ser seguidas. Está na hora de colocar a mente em ordem.`
              : `${nome} está com muitas coisas na cabeça, mas o peso não está nas lembranças: são as regras, a ficha e a conversa da rodada atual. Finalize a rodada ou reduza as regras/ficha para aliviar o contexto.`}
          </DialogDescription>
        </DialogHeader>
        {atual.memoria_util ? (
          <>
            <p className="text-sm font-medium">Acionar compressão de memória de {nome}?</p>
            <DialogFooter>
              <Button variant="outline" disabled={comprimir.isPending} onClick={proximo}>Não</Button>
              <Button
                disabled={comprimir.isPending}
                onClick={() =>
                  comprimir.mutate(nome, {
                    onSuccess: (r) => {
                      if (r.ok) toast.success(`🌬️ ${nome} respira fundo, alinha os pensamentos... o foco parece ter retornado.`)
                      else toast.error(r.mensagem)
                      proximo()
                    },
                  })
                }
              >
                {comprimir.isPending && <Loader2 className="animate-spin" />}
                {comprimir.isPending ? `${nome} organiza os pensamentos…` : 'Sim'}
              </Button>
            </DialogFooter>
          </>
        ) : (
          <DialogFooter><Button onClick={proximo}>Entendi</Button></DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}
