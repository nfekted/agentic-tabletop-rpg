import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'

// Assina o SSE da API: atualiza os dados quando a sessão muda e sabe quem está "pensando".
const PensandoContext = createContext<Set<string>>(new Set())
export const usePensando = () => useContext(PensandoContext)

export function EventosProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient()
  const [pensando, setPensando] = useState<Set<string>>(new Set())

  useEffect(() => {
    const es = new EventSource('/api/eventos')
    es.onmessage = (e) => {
      const ev = JSON.parse(e.data) as { tipo: string; agente?: string }
      if (ev.tipo === 'sessao_atualizada') {
        qc.invalidateQueries({ queryKey: ['sessao'] })
        qc.invalidateQueries({ queryKey: ['jogadores'] })
        qc.invalidateQueries({ queryKey: ['turno'] })
      } else if (ev.tipo === 'agente_respondendo' && ev.agente) {
        setPensando((s) => new Set(s).add(ev.agente!))
      } else if (ev.tipo === 'agente_pronto' && ev.agente) {
        setPensando((s) => {
          const n = new Set(s)
          n.delete(ev.agente!)
          return n
        })
      }
    }
    return () => es.close()
  }, [qc])

  return <PensandoContext.Provider value={pensando}>{children}</PensandoContext.Provider>
}
