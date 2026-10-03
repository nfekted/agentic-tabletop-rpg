// Separa o texto das respostas dos agentes ([fala], [acao], [duvida], [pensamento], [chamar]) em segmentos.
export type Segmento = { tipo: 'fala' | 'acao' | 'duvida' | 'pensamento' | 'chamar'; texto: string }

const RE = /\[(pensamento|fala|acao|duvida|chamar)\](.*?)(?:\[\/\1\]|(?=\[(?:pensamento|fala|acao|duvida)\])|$)/gis

export function parseTags(texto: string): Segmento[] {
  const segs: Segmento[] = []
  for (const m of texto.matchAll(RE)) {
    const t = m[2].trim()
    if (t) segs.push({ tipo: m[1].toLowerCase() as Segmento['tipo'], texto: t })
  }
  return segs.length ? segs : [{ tipo: 'fala', texto: texto.trim() }]
}

export const iniciais = (nome: string) => nome.slice(0, 2).toUpperCase()
