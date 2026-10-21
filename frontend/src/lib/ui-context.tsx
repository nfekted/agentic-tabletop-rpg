import { createContext, useContext } from 'react'

export type Modal =
  | { tipo: 'ficha-editar'; nome: string }
  | { tipo: 'ficha-ver'; nome: string }
  | { tipo: 'memoria'; nome: string }
  | { tipo: 'avatar'; nome: string }
  | { tipo: 'excluir-jogador'; nome: string }
  | { tipo: 'novo-jogador' }
  | { tipo: 'regras' }
  | { tipo: 'anotacoes' }
  | { tipo: 'padrao-ficha' }
  | { tipo: 'config' }
  | { tipo: 'mesas' }
  | { tipo: 'cancelar-rodada' }

export type View = 'mesa' | 'turnos' | 'tokens'

type Ctx = {
  abrir: (m: Modal) => void
  fechar: () => void
  view: View
  setView: (v: View) => void
  textoMestre: string // rascunho da Ação do mestre: compartilhado para o "desfazer" devolver a fala ao campo
  setTextoMestre: (t: string) => void
}

export const UiContext = createContext<Ctx>(null!)
export const useUi = () => useContext(UiContext)
