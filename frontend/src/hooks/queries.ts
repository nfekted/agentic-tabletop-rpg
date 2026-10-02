import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import type {
  AcaoResposta, Config, Ficha, Jogador, Memoria, Sessao, TokenCategoria, TurnoEstado, MesaSalva,
} from '@/lib/types'

export const useSessao = () => useQuery({ queryKey: ['sessao'], queryFn: () => api.get<Sessao>('/sessao') })
export const useJogadores = () =>
  useQuery({ queryKey: ['jogadores'], queryFn: () => api.get<Jogador[]>('/jogadores') })
export const useConfig = () => useQuery({ queryKey: ['config'], queryFn: () => api.get<Config>('/config') })
export const useFicha = (nome: string) =>
  useQuery({ queryKey: ['ficha', nome], queryFn: () => api.get<Ficha>(`/fichas/${nome}`), gcTime: 0 })
export const useMemoria = (nome: string) =>
  useQuery({ queryKey: ['memoria', nome], queryFn: () => api.get<Memoria>(`/memoria/${nome}`), gcTime: 0 })
export const useCenas = () => useQuery({ queryKey: ['cenas'], queryFn: () => api.get<string[]>('/cenas') })
export const useTokens = () =>
  useQuery({ queryKey: ['tokens'], queryFn: () => api.get<Record<string, TokenCategoria>>('/tokens') })
export const useRegras = () =>
  useQuery({ queryKey: ['regras'], queryFn: () => api.get<{ arquivos: string[]; ativa: string | null }>('/regras') })
export const useMesasSalvas = () =>
  useQuery({ queryKey: ['mesas'], queryFn: () => api.get<MesaSalva[]>('/mesas'), gcTime: 0 })
export const useTurno = () =>
  useQuery({ queryKey: ['turno'], queryFn: () => api.get<TurnoEstado>('/turno') })

// Ações do mestre devolvem { mensagem, sessao }: atualiza o cache e avisa o mestre.
export function useAcaoMestre<V = void>(fn: (v: V) => Promise<AcaoResposta>) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: (r) => {
      qc.setQueryData(['sessao'], r.sessao)
      qc.invalidateQueries({ queryKey: ['jogadores'] })
      if (r.mensagem) toast(r.mensagem)
    },
  })
}

// Mutação genérica: invalida as chaves informadas e, opcionalmente, avisa o resultado.
export function useAcao<V = void, R = unknown>(
  fn: (v: V) => Promise<R>,
  invalidar: string[][] = [],
  sucesso?: string | ((r: R) => string | undefined),
) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: (r) => {
      invalidar.forEach((k) => qc.invalidateQueries({ queryKey: k }))
      const msg = typeof sucesso === 'function' ? sucesso(r) : sucesso
      if (msg) toast.success(msg)
    },
  })
}
