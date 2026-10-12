export type Status = { nome: string; valor_atual: number; valor_max: number; cor: string }

export type PadraoFicha = {
  configurado: boolean
  status: { nome: string; cor: string }[]
  atributos: { nome: string }[]
}

export type Contexto = {
  usado: number
  limite: number
  pct: number
  gatilho_pct: number
  faixa: 'verde' | 'ambar' | 'vermelho'
  partes: Record<string, number>
  estimado: boolean
}

export type Jogador = {
  nome: string
  modificadores: string
  avatar_v: number | null
  status: Status[]
  contexto: Contexto | null
}

export type Fala = { seq: number; texto: string; aprovada: boolean; privado: boolean }

type PendingChamada = {
  id: string
  origem: string
  destino: string
  mensagem: string
  presentes: string[]
}

export type Sessao = {
  historico: string[]
  rodada_ativa: boolean
  pending_chamadas: PendingChamada[]
  ultima_fala: Record<string, Fala>
}

export type AcaoResposta = { mensagem: string | null; sessao: Sessao }

export type FilaItem = {
  agente: string
  status: 'pendente' | 'verificando' | 'aguardando' | 'interpretando' | 'ok' | 'erro'
  etapa: 'rodada' | 'cena' | 'mesa' | null
  tokens_previstos: number
  erro: string | null
}
export type Fila = {
  id: string
  tipo: 'falar_todos' | 'falar_direcionado' | 'aprovar_chamada' | 'finalizar_rodada'
  status: 'rodando' | 'aguardando_limite' | 'pausada' | 'concluida'
  erro: string | null
  aviso: string | null
  espera_ate: number | null
  agora: number
  indice: number
  itens: FilaItem[]
  mensagem: string | null
  limites_ativos: boolean
}

export type Limite = { limite: number; usado: number; zera_em: number; libera_em: number }
export type Limites = { rpm: Limite; tpm: Limite; rpd: Limite }

export type Config = {
  provedor: string
  base_url: string
  limite_contexto_tokens: number
  gatilho_compressao_pct: number
  alvo_reducao_pct: number
  limite_rpm: number
  limite_tpm: number
  limite_rpd: number
  api_key_definida: boolean
  provedores: string[]
}

type FichaBase = { nome: string; classe: string; passado_origem: string }
export type ParNomeValor = { nome: string; valor: string }
export type Habilidade = { nome: string; custo: string; descricao: string }
export type Habilidades = { habilidades: Habilidade[]; poderes: Habilidade[]; passivas: Habilidade[] }
export type Item = {
  nome: string
  maos: number | null
  peso: number | null
  alcance: string
  dano: string
  porcentagem_crit: number | null
  multiplicador_critico: number | null
  descricao: string
}
export type Itens = { tamanho_mochila: number; equipamento: Item[]; mochila: Item[] }
type FichaPersonalidade = {
  tratamento_personalidade: string
  medos_gatilhos: string
  segredos_pessoais: string
}

export type Ficha = {
  modificadores: string
  base: FichaBase
  status: Status[]
  atributos: ParNomeValor[]
  pericias: ParNomeValor[]
  habilidades: Habilidades
  itens: Itens
  personalidade: FichaPersonalidade
}

export type Memoria = {
  rodada_atual: string
  rodadas: { arquivo: string; conteudo: string }[]
  cenas: { arquivo: string; conteudo: string }[]
  mesa: string
}

export type TokenCategoria = {
  rotulo: string
  arquivos: { arquivo: string; tem_imagem: boolean }[]
}

type TurnoPersonagem = { id: string; nome: string; ordem: number | null }
export type TurnoToken = {
  id: string
  nome_exibicao: string
  categoria: string
  arquivo?: string
  tipo_icone: string
  ordem: number | null
  ficha_dados: { conteudo: string; status: Status[] }
}
export type TurnoArea = { id: string; nome: string; participantes: string[] }
type TurnoDados = {
  em_andamento: boolean
  ordem_atual: number | null
  areas: TurnoArea[]
  personagens: TurnoPersonagem[]
  tokens: TurnoToken[]
}
export type TurnoEstado = { ativo: boolean; turno: TurnoDados | null; empates: number[] }

export type MesaSalva = { nome: string; atualizada_em: string; tamanho: number }
