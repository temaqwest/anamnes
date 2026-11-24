import { api } from "@/shared/api"

export type Allergy = { id: string; name: string }

export function listAllergies(signal: AbortSignal) {
  return api<Allergy[]>("/allergies/", { signal })
}

export function addAllergy(name: string) {
  return api<Allergy>("/allergies/", { method: "POST", body: JSON.stringify({ name }) })
}
