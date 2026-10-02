import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

export type Campo = { chave: string; rotulo: string; dica: string }

// Conjunto fixo de campos de texto (Base e Personalidade): rótulos não são editáveis.
export function CamposFixos({
  campos, valores, onChange, multilinha,
}: {
  campos: Campo[]
  valores: Record<string, string>
  onChange: (v: Record<string, string>) => void
  multilinha?: boolean
}) {
  return (
    <div className="space-y-3">
      {campos.map((c) => (
        <div key={c.chave} className="space-y-1">
          <Label htmlFor={`campo-${c.chave}`}>{c.rotulo}</Label>
          {multilinha ? (
            <Textarea
              id={`campo-${c.chave}`} rows={3} value={valores[c.chave] ?? ''} placeholder={c.dica}
              onChange={(e) => onChange({ ...valores, [c.chave]: e.target.value })}
            />
          ) : (
            <Input
              id={`campo-${c.chave}`} value={valores[c.chave] ?? ''} placeholder={c.dica}
              onChange={(e) => onChange({ ...valores, [c.chave]: e.target.value })}
            />
          )}
        </div>
      ))}
    </div>
  )
}
