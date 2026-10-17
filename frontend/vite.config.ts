import { defineConfig } from "vite";

const audiences = ["login", "participant", "event-manager", "global"];
const local = (path: string) =>
  decodeURIComponent(new URL(path, import.meta.url).pathname).replace(
    /^\/([A-Za-z]:\/)/,
    "$1",
  );

export default defineConfig(({ mode }) => {
  const separated = audiences.includes(mode);
  return {
    base: separated && mode !== "login" ? `/spa/${mode}/` : "/",
    define: separated
      ? {
          "import.meta.env.VITE_SPA_AUDIENCE": JSON.stringify(mode),
          "import.meta.env.VITE_FRONTEND_DATA_MODE": JSON.stringify("django"),
        }
      : {},
    plugins: separated
      ? [
          {
            name: "isolated-spa",
            enforce: "pre" as const,
            transformIndexHtml: {
              order: "pre" as const,
              handler: (html: string) =>
                html.replace("/main.tsx", `/entries/${mode}.tsx`),
            },
            resolveId(source: string) {
              if (mode === "participant" && source === "./access-components")
                return local("./participant-access.ts");
              if (
                mode === "participant" &&
                source.endsWith("/administration-mock")
              )
                return local("./participant-no-admin-mock.ts");
            },
            generateBundle() {
              // Fail the build if a future import accidentally exposes another SPA.
              const forbidden =
                mode === "participant"
                  ? /\/(?:Admin[^/]*|GlobalAdministration|LoginPage|TeamManagement|Event(?:Configuration|Operations|RequestForm|ExportButton|ParticipantTopics)|ProfileTopicManagement|InitialGiftFields|administration-mock)\.(?:tsx|ts)$/
                  : mode === "event-manager"
                    ? /\/(?:GlobalAdministration|ProfileTopicManagement|App|LoginApp|useParticipant[^/]*|DiscoveryPage|MessagesPage|FiltersPage|ProfilePage|ParticipantsPage)\.(?:tsx|ts)$/
                    : mode === "login"
                      ? /\/(?:App|Administration|GlobalAdministration|ManagerApp|ParticipantOnboarding|useParticipantController)\.(?:tsx|ts)$/
                      : null;
              if (forbidden)
                for (const id of this.getModuleIds()) {
                  if (forbidden.test(id.replaceAll("\\", "/")))
                    this.error(
                      `Código de outro SPA incluído em ${mode}: ${id}`,
                    );
                }
            },
          },
        ]
      : [],
    build: separated
      ? {
          outDir: mode === "login" ? "dist/login" : `dist/spa/${mode}`,
          sourcemap: false,
          manifest: false,
          copyPublicDir: false,
        }
      : {},
    server: {
      host: "0.0.0.0",
      port: 5173,
      strictPort: true,
      proxy: {
        "/ws/": { target: "ws://backend:8000", ws: true },
        "/api/": "http://backend:8000",
        "/admin/": "http://backend:8000",
        "/static/": "http://backend:8000",
      },
    },
  };
});
