import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ImagePlus, Plus, Skull, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { useAcao, useTokens } from '@/hooks/queries'
import { api, tokenImagemUrl } from '@/lib/api'
import type { TokenCategoria } from '@/lib/types'
import { cn } from '@/lib/utils'

export function TokenThumb({ categoria, arquivo, tem, className }: { categoria: string; arquivo: string; tem: boolean; className?: string }) {
  return tem ? (
    <img src={tokenImagemUrl(categoria, arquivo)} alt="" className={cn('size-10 shrink-0 rounded-lg object-cover ring-1 ring-border', className)} />
  ) : (
    <div className={cn('flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground', className)}>
      <Skull className="size-4" />
    </div>
  )
}

function Editor({ categoria, arquivo, temImagem }: { categoria: string; arquivo: string; temImagem: boolean }) {
  const url = `/tokens/${categoria}/${encodeURIComponent(arquivo)}`
  const { data } = useQuery({ queryKey: ['token', categoria, arquivo], gcTime: 0, queryFn: () => api.get<{ conteudo: string }>(url) })
  const [texto, setTexto] = useState<string | null>(null)
  const [bust, setBust] = useState(0)
  const input = useRef<HTMLInputElement>(null)

  const salvar = useAcao(() => api.put(url, { conteudo: texto ?? data?.conteudo ?? '' }), [['token', categoria, arquivo]], 'Token salvo.')
  const excluir = useAcao(() => api.del(url), [['tokens']], 'Token excluído.')
  const enviarImg = useAcao((f: File) => { const fd = new FormData(); fd.append('imagem', f); return api.post(`${url}/imagem`, fd) },
    [['tokens']], () => { setBust(Date.now()); return 'Imagem atualizada.' })
  const removerImg = useAcao(() => api.del(`${url}/imagem`), [['tokens']], 'Imagem removida.')

  return (
    <div className="flex flex-1 flex-col gap-3">
      <div className="flex items-center gap-3">
        {temImagem
          ? <img src={tokenImagemUrl(categoria, arquivo, bust)} alt="" className="size-20 rounded-xl object-cover ring-1 ring-border" />
          : <div className="flex size-20 items-center justify-center rounded-xl bg-muted text-muted-foreground"><Skull /></div>}
        <div className="space-y-1.5">
          <p className="font-medium">{arquivo.replace(/\.txt$/, '')}</p>
          <input ref={input} type="file" accept="image/png,image/jpeg,image/webp" hidden
            onChange={(e) => { const f = e.target.files?.[0]; if (f) enviarImg.mutate(f); e.target.value = '' }} />
          <div className="flex gap-1.5">
            <Button size="sm" variant="outline" onClick={() => input.current?.click()}><ImagePlus /> Imagem</Button>
            {temImagem && <Button size="sm" variant="ghost" onClick={() => removerImg.mutate()}>Remover</Button>}
          </div>
        </div>
      </div>
      <Textarea value={texto ?? data?.conteudo ?? ''} onChange={(e) => setTexto(e.target.value)} rows={14}
        className="min-h-60 flex-1 font-mono text-[13px]" disabled={!data} placeholder="Anotações, ficha ou prompt pronto para copiar…" />
      <div className="flex gap-2">
        <Button disabled={texto === null || salvar.isPending} onClick={() => salvar.mutate()}>Salvar</Button>
        <Button variant="outline" className="ml-auto" onClick={() => excluir.mutate()}><Trash2 /> Excluir</Button>
      </div>
    </div>
  )
}

function Categoria({ id, cat }: { id: string; cat: TokenCategoria }) {
  const [sel, setSel] = useState<string | null>(null)
  const [novo, setNovo] = useState('')
  const atual = cat.arquivos.find((a) => a.arquivo === sel) ?? cat.arquivos[0]
  const criar = useAcao(() => api.post<{ arquivo: string }>(`/tokens/${id}`, { nome: novo }), [['tokens']], 'Token criado.')

  return (
    <div className="grid gap-4 md:grid-cols-[16rem_1fr]">
      <div className="space-y-2">
        <div className="max-h-72 space-y-1 overflow-y-auto md:max-h-[60vh]">
          {cat.arquivos.map((a) => (
            <button key={a.arquivo} onClick={() => setSel(a.arquivo)}
              className={cn('flex w-full items-center gap-2 rounded-lg border p-1.5 text-left text-sm hover:bg-muted', atual?.arquivo === a.arquivo && 'border-primary bg-muted')}>
              <TokenThumb categoria={id} arquivo={a.arquivo} tem={a.tem_imagem} className="size-8" />
              <span className="truncate">{a.arquivo.replace(/\.txt$/, '')}</span>
            </button>
          ))}
        </div>
        <div className="flex gap-1.5">
          <Input value={novo} onChange={(e) => setNovo(e.target.value)} placeholder={`Novo ${cat.rotulo.toLowerCase()}`}
            onKeyDown={(e) => e.key === 'Enter' && novo.trim() && criar.mutate(undefined, { onSuccess: (r) => { setNovo(''); setSel(r.arquivo) } })} />
          <Button size="icon" variant="secondary" aria-label="Criar" disabled={!novo.trim() || criar.isPending}
            onClick={() => criar.mutate(undefined, { onSuccess: (r) => { setNovo(''); setSel(r.arquivo) } })}><Plus /></Button>
        </div>
      </div>
      {atual
        ? <Editor key={`${id}/${atual.arquivo}`} categoria={id} arquivo={atual.arquivo} temImagem={atual.tem_imagem} />
        : <p className="text-sm text-muted-foreground">Nada aqui ainda — crie o primeiro.</p>}
    </div>
  )
}

export function TokensView() {
  const { data } = useTokens()
  if (!data) return <p className="text-sm text-muted-foreground">Carregando…</p>
  const ids = Object.keys(data)
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">👾 Inimigos, NPCs e Itens</h1>
        <p className="text-sm text-muted-foreground">Anotações e imagens reutilizáveis. No modo por turnos entram como cópias isoladas.</p>
      </div>
      <Tabs defaultValue={ids[0]}>
        <TabsList>{ids.map((id) => <TabsTrigger key={id} value={id}>{data[id].rotulo} ({data[id].arquivos.length})</TabsTrigger>)}</TabsList>
        {ids.map((id) => <TabsContent key={id} value={id} className="pt-2"><Categoria id={id} cat={data[id]} /></TabsContent>)}
      </Tabs>
    </div>
  )
}
