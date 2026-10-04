/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_FRONTEND_DATA_MODE?: "mock" | "django";
}
