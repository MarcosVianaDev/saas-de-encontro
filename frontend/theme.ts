import darkThemeCss from "./dark-theme.css?inline";

export type ThemeMode = "light" | "dark" | "auto";
const storageKey = "eventconnect-theme";
const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
const listeners = new Set<() => void>();
const isThemeMode = (value: unknown): value is ThemeMode =>
  value === "light" || value === "dark" || value === "auto";

function readPreference(): ThemeMode {
  try {
    const value = localStorage.getItem(storageKey);
    return isThemeMode(value) ? value : "auto";
  } catch {
    return "auto";
  }
}

let mode = readPreference();
const style = document.createElement("style");
style.id = "eventconnect-dark-theme";
style.textContent = darkThemeCss;
document.head.append(style);

function applyTheme() {
  const dark = mode === "dark" || (mode === "auto" && systemTheme.matches);
  const resolved = dark ? "dark" : "light";
  style.media = dark ? "all" : "not all";
  document.documentElement.dataset.bsTheme = resolved;
  document.documentElement.dataset.theme = resolved;
  document.documentElement.style.colorScheme = resolved;
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", dark ? "#101522" : "#fefbff");
}

applyTheme();
systemTheme.addEventListener("change", () => {
  if (mode === "auto") applyTheme();
});
window.addEventListener("storage", (event) => {
  if (event.key !== storageKey && event.key !== null) return;
  mode = readPreference();
  applyTheme();
  listeners.forEach((listener) => listener());
});

export const getThemeMode = () => mode;
export function subscribeTheme(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
export function setThemeMode(value: ThemeMode) {
  mode = value;
  try { localStorage.setItem(storageKey, value); } catch { /* Keep the choice for this session. */ }
  applyTheme();
  listeners.forEach((listener) => listener());
}
