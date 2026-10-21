import { useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { Carregando } from '@/components/Carregando'
import { DialogAberto } from '@/components/DialogAberto'
import { TaggedText } from '@/components/TaggedText'
import { Button } from '@/components/ui/button'
import {
  DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { useAcao, useJogadores } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { GrupoCombate, TrechosCombate } from '@/lib/types'
import { cn } from '@/lib/utils'

const chave = (g: GrupoCombate) => g.agentes.join('|')

// Uma mensagem começa numa linha "Autor: ..." (Mestre, Resumo ou jogador); as demais linhas continuam a anterior.
function Trecho({ texto, nomes }: { texto: string; nomes: string[] }) {
  if (!texto) return <p className="text-sm text-muted-foreground">Nada registrado depois da marca ainda.</p>
  const inicio = (linha: string) => {
    const k = linha.indexOf(':')
    if (k < 0) return null
    const autor = linha.slice(0, k).trim()
    const base = autor.replace(/\s*\(.*\)$/, '')
    return base === 'Mestre' || base === 'Resumo do combate' || nomes.includes(base) ? { autor, resto: linha.slice(k + 1).trim() } : null
  }
  const msgs: { autor: string; linhas: string[] }[] = []
  for (const linha of texto.split('\n')) {
    const m = inicio(linha)
    if (m) msgs.push({ autor: m.autor, linhas: [m.resto] })
    else if (msgs.length) msgs[msgs.length - 1].linhas.push(linha)
    else msgs.push({ autor: 'Mestre', linhas: [linha] })
  }
  return (
    <div className="space-y-1.5">
      {msgs.map((m, i) => {
        const mestre = m.autor.startsWith('Mestre') || m.autor.startsWith('Resumo')
        return (
          <div key={i} className={cn('rounded-xl px-2.5 py-1.5 text-sm', mestre ? 'bg-primary/15' : 'bg-muted')}>
            <p className="text-xs font-semibold text-muted-foreground">{m.autor}</p>
            <TaggedText texto={m.linhas.join('\n')} plano={mestre} />
          </div>
        )
      })}
    </div>
  )
}

// Resume o que aconteceu desde [INICIO COMBATE]: o texto escrito substitui o trecho na memória e no histórico.
// `encerrar`: o modo por turnos será encerrado depois (aplicando o resumo ou não).
export function ResumoCombateDialog({ encerrar, onFechar, onConcluir }: {
  encerrar: boolean; onFechar: () => void; onConcluir: () => void
}) {
  const qc = useQueryClient()
  const nomes = (useJogadores().data ?? []).map((j) => j.nome)
  const { data } = useQuery({
    queryKey: ['combate-trechos'], gcTime: 0, staleTime: 0,
    queryFn: () => api.get<TrechosCombate>('/turno/combate/trechos'),
  })
  const [resumos, setResumos] = useState<Record<string, string>>({})
  const [sugerindo, setSugerindo] = useState<string | null>(null)

  const vazio = !!data && (!data.marcado || data.grupos.every((g) => g.chars === 0))
  // ao encerrar sem nada a resumir, o diálogo nem aparece
  const encerrado = useRef(false)
  useEffect(() => {
    if (encerrar && vazio && !encerrado.current) { encerrado.current = true; onConcluir() }
  }, [encerrar, vazio, onConcluir])

  const aplicar = useAcao(
    () => api.post('/turno/combate/resumo', {
      grupos: (data?.grupos ?? []).map((g) => ({ agentes: g.agentes, resumo: resumos[chave(g)] ?? '' })),
    }),
    [['sessao'], ['jogadores'], ['combate-trechos']], 'Resumo do combate aplicado.',
  )
  const sugerir = async (g: GrupoCombate) => {
    setSugerindo(chave(g))
    try {
      const r = await api.post<{ resumo: string }>('/turno/combate/sugerir', { agente: g.agentes[0] })
      if (r.resumo) setResumos((x) => ({ ...x, [chave(g)]: r.resumo }))
      else toast.warning('Nada a resumir ainda.')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Não foi possível sugerir o resumo.')
    } finally {
      setSugerindo(null)
    }
  }
  const algum = Object.values(resumos).some((r) => r.trim())
  const concluir = () => { qc.invalidateQueries({ queryKey: ['combate-trechos'] }); onConcluir() }

  return (
    <DialogAberto onFechar={onFechar}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle>⚔️ Contexto atual do combate</DialogTitle>
          <DialogDescription>
            Tudo desde o início do combate está à esquerda. O que você escrever à direita substitui esse trecho na memória
            dos jogadores e no histórico. Deixe em branco para manter como está.
          </DialogDescription>
        </DialogHeader>
        {!data || (encerrar && vazio) ? <Carregando /> : data.grupos.length === 0 ? (
          <p className="text-sm text-muted-foreground">O combate ainda não foi marcado (inicie o combate com uma rodada ativa).</p>
        ) : (
          <Tabs defaultValue={chave(data.grupos[0])}>
            {data.grupos.length > 1 && (
              <>
                <p className="text-xs text-muted-foreground">
                  Há conteúdo diferente entre os jogadores (mensagem privada). Cada aba é resumida separadamente.
                </p>
                <TabsList variant="line" className="w-full flex-wrap justify-start">
                  {data.grupos.map((g) => (
                    <TabsTrigger key={chave(g)} value={chave(g)} className="flex-none px-3">{g.agentes.join(', ')}</TabsTrigger>
                  ))}
                </TabsList>
              </>
            )}
            {data.grupos.map((g) => (
              <TabsContent key={chave(g)} value={chave(g)} className="grid gap-3 md:grid-cols-2">
                <div className="max-h-[50vh] overflow-y-auto rounded-xl border p-2">
                  <Trecho texto={g.texto} nomes={nomes} />
                </div>
                <div className="flex flex-col gap-2">
                  <Textarea rows={12} className="min-h-48 flex-1" value={resumos[chave(g)] ?? ''}
                    onChange={(e) => setResumos((x) => ({ ...x, [chave(g)]: e.target.value }))}
                    placeholder="Descreva narrativamente os acontecimentos desse turno" />
                  <Button variant="outline" size="sm" className="self-start" disabled={!g.chars || sugerindo !== null} onClick={() => sugerir(g)}>
                    {sugerindo === chave(g) ? <Loader2 className="animate-spin" /> : <Sparkles />} Sugerir resumo
                  </Button>
                </div>
              </TabsContent>
            ))}
          </Tabs>
        )}
        <DialogFooter>
          {encerrar ? (
            <>
              <Button variant="outline" onClick={onFechar}>Voltar</Button>
              <Button variant="outline" onClick={concluir}>Encerrar sem resumir</Button>
              <Button disabled={!algum || aplicar.isPending} onClick={() => aplicar.mutate(undefined, { onSuccess: concluir })}>
                Resumir e encerrar
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={onFechar}>Ignorar</Button>
              <Button disabled={!algum || aplicar.isPending} onClick={() => aplicar.mutate(undefined, { onSuccess: onFechar })}>
                Aplicar resumo
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </DialogAberto>
  )
}
