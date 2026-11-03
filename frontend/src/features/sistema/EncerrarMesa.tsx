import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DialogAberto } from '@/components/DialogAberto'
import { DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useAcao, useJogadores, useSessao } from '@/hooks/queries'
import { api } from '@/lib/api'

// Fim de missão: compila a memória de cada personagem vivo até o mesa.txt e, se pedido, sugere o resumo da
// missão como "passado" para você revisar e gravar em "Missões anteriores" da ficha.
export function EncerrarMesa({ onFechar }: { onFechar: () => void }) {
  const qc = useQueryClient()
  const vivos = (useJogadores().data ?? []).filter((j) => !j.morto).map((j) => j.nome)
  const rodadaAtiva = !!useSessao().data?.rodada_ativa
  const [gerar, setGerar] = useState(true)
  const [titulo, setTitulo] = useState('')
  const [feitos, setFeitos] = useState<string[]>([])
  const [rodando, setRodando] = useState(false)
  const [resumos, setResumos] = useState<Record<string, string> | null>(null)

  const encerrar = useAcao((nome: string) => api.post<{ resumo: string }>(`/memoria/${nome}/encerrar`, { gerar }), [['jogadores']])
  const gravar = useAcao(
    async () => {
      for (const [nome, texto] of Object.entries(resumos ?? {}))
        if (texto.trim()) await api.post(`/fichas/${nome}/missao`, { texto, titulo: titulo.trim() })
    },
    [['ficha']], 'Resumos gravados em "Missões anteriores".',
  )

  async function iniciar() {
    setRodando(true)
    setFeitos([])
    const saida: Record<string, string> = {}
    try {
      for (const nome of vivos) {
        saida[nome] = (await encerrar.mutateAsync(nome)).resumo
        setFeitos((f) => [...f, nome])
      }
    } catch {
      setRodando(false) // o erro já foi avisado; quem terminou está compilado e a ação pode ser repetida
      return
    }
    qc.invalidateQueries()
    setRodando(false)
    if (gerar) setResumos(saida)
    else onFechar()
  }

  return (
    <DialogAberto onFechar={() => !rodando && onFechar()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>🏁 Encerrar mesa</DialogTitle>
          <DialogDescription>
            Para cada personagem vivo, as rodadas viram cena e as cenas entram no histórico (mesa.txt).
            A mesa não é apagada; para começar outra, use depois “Importar base”.
          </DialogDescription>
        </DialogHeader>

        {!resumos ? (
          <div className="space-y-3 text-sm">
            {rodadaAtiva && <p className="text-amber-300">Há uma rodada em andamento. Encerre-a antes de encerrar a mesa.</p>}
            <label className="flex items-start gap-2">
              <input type="checkbox" className="mt-1" checked={gerar} disabled={rodando} onChange={(e) => setGerar(e.target.checked)} />
              <span>
                Gerar resumo da mesa
                <span className="block text-xs text-muted-foreground">
                  Uma chamada à LLM por personagem, a partir do mesa.txt: a missão contada como passado dele. Você revisa antes de gravar.
                </span>
              </span>
            </label>
            <div className="space-y-1.5">
              <Label htmlFor="titulo-missao">Título da missão (opcional)</Label>
              <Input id="titulo-missao" value={titulo} disabled={rodando} onChange={(e) => setTitulo(e.target.value)} placeholder="Ex.: O caso do farol" />
            </div>
            {rodando && (
              <p className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="size-4 animate-spin" /> Organizando a memória… {feitos.length}/{vivos.length}
                {feitos.length < vivos.length && ` (${vivos[feitos.length]})`}
              </p>
            )}
            <DialogFooter>
              <Button variant="outline" disabled={rodando} onClick={onFechar}>Fechar</Button>
              <Button disabled={rodando || rodadaAtiva || vivos.length === 0} onClick={iniciar}>
                {gerar ? 'Compilar e gerar resumos' : 'Compilar memória'}
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Revise e edite. Cada texto é acrescentado ao fim de “Missões anteriores” na ficha; deixe em branco para pular um personagem.
            </p>
            {Object.entries(resumos).map(([nome, texto]) => (
              <div key={nome} className="space-y-1.5">
                <Label htmlFor={`resumo-${nome}`}>{nome}</Label>
                <Textarea id={`resumo-${nome}`} value={texto} className="min-h-28"
                  placeholder="Sem histórico para resumir; escreva à mão ou deixe em branco."
                  onChange={(e) => setResumos({ ...resumos, [nome]: e.target.value })} />
              </div>
            ))}
            <DialogFooter>
              <Button variant="outline" disabled={gravar.isPending} onClick={onFechar}>Fechar sem gravar</Button>
              <Button disabled={gravar.isPending} onClick={() => gravar.mutate(undefined, { onSuccess: onFechar })}>Gravar nas fichas</Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </DialogAberto>
  )
}
