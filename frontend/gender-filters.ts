import type { Filters } from "./types";

export const genderOptions = [
  { value: "Mulheres", label: "Mulheres" },
  { value: "Homens", label: "Homens" },
  { value: "Não binário", label: "Não binários" },
] as const;

const prefix = "eventconnect-gender-filters:";
const preferences = new Map<string, string[]>();

export function selectedGenders(filters: Filters): string[] {
  return filters.genders ?? (filters.gender === "Todos" ? [] : [filters.gender]);
}

export function matchesGender(gender: string, filters: Filters): boolean {
  const selected = selectedGenders(filters);
  return selected.length === 0 || selected.includes(gender);
}

export function restoreGenderFilters(eventId: string, filters: Filters): Filters {
  let selected = preferences.get(eventId);
  if (!selected) {
    try {
      const stored: unknown = JSON.parse(sessionStorage.getItem(prefix + eventId) || "null");
      if (Array.isArray(stored) && stored.every((value) => genderOptions.some((option) => option.value === value))) {
        selected = stored;
      }
    } catch { /* Use the current selection when storage is unavailable. */ }
  }
  return { ...filters, genders: selected ?? selectedGenders(filters) };
}

export function saveGenderFilters(eventId: string, filters: Filters) {
  const selected = [...selectedGenders(filters)];
  preferences.set(eventId, selected);
  try { sessionStorage.setItem(prefix + eventId, JSON.stringify(selected)); } catch { /* Keep the preference in memory. */ }
}

export function clearGenderFilters() {
  preferences.clear();
  try {
    Object.keys(sessionStorage).filter((key) => key.startsWith(prefix)).forEach((key) => sessionStorage.removeItem(key));
  } catch { /* Storage may be unavailable. */ }
}
