export function formatStudyDate(iso: string): string {
  const [year, month, day] = iso.split("-")
  return [day, month, year].join(".")
}
