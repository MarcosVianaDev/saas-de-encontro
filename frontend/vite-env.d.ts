/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SPA_AUDIENCE?: "login" | "participant" | "event-manager" | "global";
  readonly VITE_FRONTEND_DATA_MODE?: "mock" | "django";
}
