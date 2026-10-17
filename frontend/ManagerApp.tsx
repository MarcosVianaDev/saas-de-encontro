import { useEffect, useState } from "react";
import { Administration } from "./Administration";
import { api, ApiError } from "./backend-client";
import { clearImageCache } from "./CachedImage";
import { routeOutsideSpa } from "./spa-routing";

export function App() {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    void (async () => {
      try {
        const session = await api.session();
        if (!session.authenticated) {
          location.replace("/");
          return;
        }
        const data = await api.bootstrap();
        if (routeOutsideSpa(data)) return;
        if (data.navigation !== "administration") {
          location.replace("/");
          return;
        }
        if (!location.hash.startsWith("#admin-"))
          location.hash = `admin-${data.initialPage || "dashboard"}`;
        setReady(true);
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) location.replace("/");
        else
          setError(
            e instanceof Error ? e.message : "Não foi possível conectar.",
          );
      }
    })();
  }, []);
  if (!ready)
    return (
      <main className="adm-loading">
        <p role={error ? "alert" : "status"}>{error || "Carregando painel…"}</p>
        {error && <a href="/">Voltar ao acesso</a>}
      </main>
    );
  return (
    <Administration
      onLogout={async () => {
        await api.logout();
        clearImageCache();
        location.replace("/");
      }}
    />
  );
}
