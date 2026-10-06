export function InputCor({ value, onChange }: { value: string; onChange: (cor: string) => void }) {
  return (
    <input
      type="color" value={value} onChange={(e) => onChange(e.target.value)}
      className="h-8 w-full cursor-pointer rounded-md border bg-transparent" aria-label="Cor"
    />
  )
}
