export type FrontendDataMode = "mock" | "django";

const configuredMode = import.meta.env.VITE_FRONTEND_DATA_MODE ?? "mock";
if (configuredMode !== "mock" && configuredMode !== "django") {
  throw new Error("FRONTEND_DATA_MODE deve ser mock ou django.");
}
const isDemonstration = new URLSearchParams(location.search).get("demo") === "1";
const mode = isDemonstration ? "mock" : configuredMode;

export const frontendConfig = {
  dataMode: mode as FrontendDataMode,
  useMocks: mode === "mock",
  isDemonstration,
};
