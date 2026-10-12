import { useEffect } from 'react'
import { toast } from 'sonner'
import { useFila } from '@/hooks/queries'

// Mostra uma única vez o resultado de uma fila concluída (as ações agora rodam em segundo plano).
export function FilaAviso() {
  const { data: fila } = useFila()
  const id = fila?.status === 'concluida' ? fila.id : null
  const mensagem = fila?.mensagem

  useEffect(() => {
    if (!id) return
    try {
      if (sessionStorage.getItem('fila-avisada') === id) return
      sessionStorage.setItem('fila-avisada', id)
    } catch { /* sem sessionStorage: pode repetir o aviso */ }
    if (mensagem) toast(mensagem)
  }, [id, mensagem])

  return null
}
