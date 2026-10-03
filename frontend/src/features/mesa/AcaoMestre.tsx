import { useRef, useState } from 'react'
import { ImagePlus, Library, Loader2, Send, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useAcaoMestre, useJogadores } from '@/hooks/queries'
import { usePensando } from '@/hooks/eventos'
import { api } from '@/lib/api'
import type { AcaoResposta } from '@/lib/types'
import { cn } from '@/lib/utils'
import { CenasDialog } from './CenasDialog'

type Modo = 'todos' | 'especificos' | 'privada'
const MODOS: { id: Modo; rotulo: string; dica: string }[] = [
  { id: 'todos', rotulo: 'Todos (público)', dica: 'A mesa toda ouve e todos respondem.' },
  { id: 'especificos', rotulo: 'Jogadores específicos', dica: 'A mesa toda ouve, mas só o jogador escolhido responde.' },
  { id: 'privada', rotulo: 'Cena privada', dica: 'Só os selecionados ouvem, lembram e respondem.' },
]

async function enviar(modo: Modo, texto: string, alvos: string[], imagem: File | null) {
  const fd = new FormData()
  fd.append('comando', texto)
  if (imagem) fd.append('imagem', imagem)
  if (modo === 'todos') return api.post<AcaoResposta>('/mestre/falar-todos', fd)
  alvos.forEach((a) => fd.append('alvos', a))
  fd.append('privado', String(modo === 'privada'))
  return api.post<AcaoResposta>('/mestre/falar-direcionado', fd)
}

export function AcaoMestre() {
  const { data: jogadores = [] } = useJogadores()
  const pensando = usePensando()
  const [modo, setModo] = useState<Modo>('todos')
  const [alvos, setAlvos] = useState<string[]>([])
  const [texto, setTexto] = useState('')
  const [imagem, setImagem] = useState<File | null>(null)
  const [cenas, setCenas] = useState(false)
  const inputImg = useRef<HTMLInputElement>(null)

  const envio = useAcaoMestre(() => enviar(modo, texto.trim(), alvos, imagem))
  const podeEnviar = texto.trim() && (modo === 'todos' || alvos.length > 0) && !envio.isPending

  // Jogadores específicos: um único alvo. Cena privada: um grupo.
  const alternar = (n: string) =>
    setAlvos((a) => (a.includes(n) ? a.filter((x) => x !== n) : modo === 'especificos' ? [n] : [...a, n]))
  const enviarAgora = () =>
    envio.mutate(undefined, {
      onSuccess: () => { setTexto(''); setImagem(null); if (inputImg.current) inputImg.current.value = '' },
    })

  return (
    <section className="space-y-3 rounded-2xl border bg-card p-4">
      <h2 className="font-semibold">🎲 Ação do mestre</h2>

      <div className="flex flex-wrap gap-1.5" role="radiogroup" aria-label="Destinatário">
        {MODOS.map((m) => (
          <button
            key={m.id}
            role="radio"
            aria-checked={modo === m.id}
            title={m.dica}
            onClick={() => { setModo(m.id); if (m.id === 'especificos') setAlvos((a) => a.slice(0, 1)) }}
            className={cn(
              'rounded-full border px-3 py-1 text-sm transition-colors',
              modo === m.id ? 'border-primary bg-primary/15 text-primary' : 'hover:bg-muted',
            )}
          >
            {m.rotulo}
          </button>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">{MODOS.find((m) => m.id === modo)!.dica}</p>

      {modo !== 'todos' && (
        <div className="flex flex-wrap gap-1.5">
          {jogadores.map((j) => {
            const idx = alvos.indexOf(j.nome)
            return (
              <button
                key={j.nome}
                onClick={() => alternar(j.nome)}
                className={cn(
                  'rounded-lg border px-2.5 py-1 text-sm',
                  idx >= 0 ? 'border-primary bg-primary/15 text-primary' : 'hover:bg-muted',
                )}
              >
                {idx >= 0 && <span className="mr-1 text-xs opacity-70">{idx + 1}º</span>}
                {j.nome}
              </button>
            )
          })}
          {jogadores.length === 0 && <p className="text-sm text-muted-foreground">Adicione jogadores primeiro.</p>}
        </div>
      )}

      <Textarea
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && podeEnviar) enviarAgora() }}
        placeholder="O que o mestre diz ou descreve? (Ctrl+Enter envia)"
        rows={4}
        disabled={envio.isPending}
      />

      <div className="flex flex-wrap items-center gap-2">
        <input
          ref={inputImg}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          hidden
          onChange={(e) => setImagem(e.target.files?.[0] ?? null)}
        />
        <Button variant="outline" size="sm" onClick={() => inputImg.current?.click()}>
          <ImagePlus /> Imagem de contexto
        </Button>
        {imagem && (
          <span className="flex items-center gap-1 rounded-lg bg-muted px-2 py-1 text-xs">
            {imagem.name}
            <button onClick={() => { setImagem(null); if (inputImg.current) inputImg.current.value = '' }} aria-label="Remover imagem">
              <X className="size-3" />
            </button>
          </span>
        )}
        <Button variant="outline" size="sm" onClick={() => setCenas(true)}>
          <Library /> Cenas
        </Button>
        <Button className="ml-auto" disabled={!podeEnviar} onClick={enviarAgora}>
          {envio.isPending ? <Loader2 className="animate-spin" /> : <Send />}
          {envio.isPending ? 'Aguardando…' : 'Enviar'}
        </Button>
      </div>
      {envio.isPending && pensando.size > 0 && (
        <p className="text-xs text-muted-foreground">Respondendo: {[...pensando].join(', ')}…</p>
      )}

      <CenasDialog aberto={cenas} onFechar={() => setCenas(false)} textoAtual={texto} onUsar={setTexto} />
    </section>
  )
}
