import { createContext, useContext } from 'react'

// Modais globais abertos a partir de qualquer tela (cards, sidebar, turno...).
export type Modal =
  | { tipo: 'ficha-editar'; nome: string }
  | { tipo: 'ficha-ver'; nome: string }
  | { tipo: 'memoria'; nome: string }
  | { tipo: 'avatar'; nome: string }
  | { tipo: 'excluir-jogador'; nome: string }
  | { tipo: 'novo-jogador' }
  | { tipo: 'regras' }
  | { tipo: 'config' }
  | { tipo: 'mesas' }
  | { tipo: 'cancelar-rodada' }

export type View = 'mesa' | 'turnos' | 'tokens'

type Ctx = {
  abrir: (m: Modal) => void
  fechar: () => void
  view: View
  setView: (v: View) => void
}

export const UiContext = createContext<Ctx>(null!)
export const useUi = () => useContext(UiContext)
