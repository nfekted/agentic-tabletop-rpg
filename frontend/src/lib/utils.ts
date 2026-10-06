import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const patchAt = <T>(lista: T[], i: number, patch: Partial<T>) =>
  lista.map((x, k) => (k === i ? { ...x, ...patch } : x))

export const removeAt = <T>(lista: T[], i: number) => lista.filter((_, k) => k !== i)

export const semTxt = (nome: string) => nome.replace(/\.txt$/, '')

export const IMAGENS_ACEITAS = 'image/png,image/jpeg,image/webp'
