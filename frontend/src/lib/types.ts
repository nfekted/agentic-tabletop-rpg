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
  passou_gatilho: boolean
  faixa: 'verde' | 'ambar' | 'vermelho'
  partes: Record<string, number>
  estimado: boolean
  medicao_id: number
  atualizado_em: string
}

export type Jogador = {
  nome: string
  modificadores: string
  avatar_v: number | null
  status: Status[]
  contexto: Contexto | null
}

export type Tags = {
  pensamento?: string | null
  fala?: string | null
  acao?: string | null
  duvida?: string | null
}

export type Fala = { seq: number; texto: string; aprovada: boolean; privado: boolean }

export type PendingPrincipal = {
  alvo: string
  resposta_completa: string
  conteudo_publico: string
  tags: Tags
  presentes: string[]
  agentes_alvo_log: string[]
}

export type AguardandoRedirect = {
  candidatos: string[]
  alvo_principal: string
  resposta_pergunta: string
  agentes_alvo_log: string[]
}

export type PendingRedirect = {
  id: string
  destino: string
  resposta_completa: string
  conteudo_publico: string
  tags: Tags
  alvo_principal: string
  agentes_alvo_log: string[]
}

export type Sessao = {
  historico: string[]
  rodada_ativa: boolean
  envolvidos: string[]
  pending_principal: PendingPrincipal | null
  aguardando_redirect: AguardandoRedirect | null
  pending_redirects: PendingRedirect[]
  ultima_fala: Record<string, Fala>
  seq_fala: number
}

export type AcaoResposta = { mensagem: string | null; sessao: Sessao }

export type Config = {
  provedor: string
  base_url: string
  limite_contexto_tokens: number
  gatilho_compressao_pct: number
  alvo_reducao_pct: number
  api_key_definida: boolean
  provedores: string[]
}

export type FichaBase = { nome: string; classe: string; passado_origem: string }
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
export type FichaPersonalidade = {
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

export type TurnoPersonagem = { id: string; nome: string; ordem: number | null }
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
export type TurnoDados = {
  em_andamento: boolean
  ordem_atual: number | null
  areas: TurnoArea[]
  personagens: TurnoPersonagem[]
  tokens: TurnoToken[]
}
export type TurnoEstado = { ativo: boolean; turno: TurnoDados | null; empates: number[] }

export type MesaSalva = { nome: string; atualizada_em: string; tamanho: number }
