export type FrontendDataMode = "mock" | "django";

const mode = import.meta.env.VITE_FRONTEND_DATA_MODE ?? "mock";
if (mode !== "mock" && mode !== "django") {
  throw new Error("FRONTEND_DATA_MODE deve ser mock ou django.");
}

export const frontendConfig = {
  dataMode: mode as FrontendDataMode,
  useMocks: mode === "mock",
};
