export type FrontendDataMode = "mock" | "debug";

const mode = import.meta.env.VITE_FRONTEND_DATA_MODE ?? "mock";
if (mode !== "mock" && mode !== "debug") {
  throw new Error("FRONTEND_DATA_MODE deve ser mock ou debug.");
}

export const frontendConfig = {
  dataMode: mode as FrontendDataMode,
  useMocks: mode === "mock",
};
