import type { Ficha, Item } from './types'
import { semAcento } from './utils'

export type Detalhe = { tipo: string; nome: string; texto: string }

const BLOCOS = [['habilidades', 'Habilidade'], ['poderes', 'Poder'], ['passivas', 'Passiva']] as const

function textoItem(i: Item): string {
  const crit = i.porcentagem_crit != null || i.multiplicador_critico != null
  return [
    i.peso != null && `Peso: ${i.peso}`,
    i.maos != null && `Mãos: ${i.maos}`,
    i.alcance && `Alcance: ${i.alcance}`,
    i.dano && `Dano: ${i.dano}`,
    crit && `Crítico: ${i.porcentagem_crit ?? '-'}% x${i.multiplicador_critico ?? '-'}`,
    i.descricao && `Descrição: ${i.descricao}`,
  ].filter((l): l is string => !!l).join('\n')
}

// Habilidades, poderes, passivas e itens da ficha cujo nome aparece no texto (sem diferenciar acento, caixa ou plural simples).
export function acharDetalhes(ficha: Ficha, texto: string): Detalhe[] {
  const alvo = semAcento(texto)
  const citado = (nome: string) => {
    const n = semAcento(nome.trim()).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    return n.length >= 3 && new RegExp(`(^|[^a-z0-9])${n}s?([^a-z0-9]|$)`).test(alvo)
  }
  const candidatos: Detalhe[] = [
    ...BLOCOS.flatMap(([chave, tipo]) => ficha.habilidades[chave].map((h) => ({
      tipo, nome: h.nome, texto: [h.custo && `Custo: ${h.custo}`, h.descricao].filter(Boolean).join('\n'),
    }))),
    ...ficha.itens.equipamento.map((i) => ({ tipo: 'Equipado', nome: i.nome, texto: textoItem(i) })),
    ...ficha.itens.mochila.map((i) => ({ tipo: 'Mochila', nome: i.nome, texto: textoItem(i) })),
  ]
  const vistos = new Set<string>()
  return candidatos.filter((d) => {
    const chave = `${d.tipo}:${d.nome}`
    if (vistos.has(chave) || !citado(d.nome)) return false
    vistos.add(chave)
    return true
  })
}
