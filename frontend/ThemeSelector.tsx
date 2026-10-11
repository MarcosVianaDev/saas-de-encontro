import { useSyncExternalStore } from "react";
import Dropdown from "react-bootstrap/Dropdown";
import { getThemeMode, setThemeMode, subscribeTheme, type ThemeMode } from "./theme";

const options: { value: ThemeMode; label: string }[] = [
  { value: "light", label: "Claro" },
  { value: "dark", label: "Escuro" },
  { value: "auto", label: "Automático" },
];

function ThemeIcon({ mode }: { mode: ThemeMode }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {mode === "light" ? <>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" />
      </> : mode === "dark" ? (
        <path d="M20.5 14.5A9 9 0 0 1 9.5 3.5a9 9 0 1 0 11 11Z" />
      ) : <>
        <path d="M12 6a6 6 0 0 0 0 12V6Zm0 0a6 6 0 0 1 0 12 7 7 0 0 0 0-12ZM12 2v2m0 16v2M2 12h2M5 5l1.5 1.5M5 19l1.5-1.5" />
      </>}
    </svg>
  );
}

export function ThemeSelector() {
  const mode = useSyncExternalStore(subscribeTheme, getThemeMode);
  const selected = options.find((option) => option.value === mode)!;
  return (
    <Dropdown className="profile-theme-selector" align="end">
      <Dropdown.Toggle type="button" variant="" className="profile-theme-toggle" aria-label={`Tema: ${selected.label}`}>
        <ThemeIcon mode={mode} />
      </Dropdown.Toggle>
      <Dropdown.Menu aria-label="Selecionar tema">
        {options.map((option) => (
          <Dropdown.Item as="button" type="button" key={option.value} active={mode === option.value} aria-pressed={mode === option.value} onClick={() => setThemeMode(option.value)}>
            <ThemeIcon mode={option.value} />
            <span>{option.label}</span>
          </Dropdown.Item>
        ))}
      </Dropdown.Menu>
    </Dropdown>
  );
}
