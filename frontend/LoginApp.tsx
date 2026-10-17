import { useEffect, useState } from "react";
import { api, request } from "./backend-client";
import { Contexts } from "./Contexts";
import { LoginPage } from "./views/LoginPage";
import { enterSpa } from "./spa-routing";
import type { Context, SessionData } from "./types";

export function App() {
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [contexts, setContexts] = useState<Context[] | null>(null);
  const invite = new URLSearchParams(location.search).get("invite");
  const invitePath = `join/${encodeURIComponent(invite || "")}/`;

  const accept = async (data: SessionData) => {
    if (data.navigation === "selection") setContexts(data.contexts);
    else await enterSpa();
  };

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const session = await api.session();
        if (invite) {
          const event = await request<{ name: string }>(invitePath);
          if (active) setInviteName(event.name);
        }
        if (!active) return;
        if (session.authenticated) {
          if (invite) await request(invitePath, "POST");
          await accept(await api.bootstrap());
        }
      } catch (e) {
        if (active)
          setError(
            e instanceof Error ? e.message : "Não foi possível conectar.",
          );
      } finally {
        if (active) setReady(true);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const loginSubmit = async (
    email: string,
    password: string,
    register: boolean,
  ) => {
    if (busy || !ready) return;
    setBusy(true);
    setError("");
    try {
      await api.session();
      await accept(
        await api.login(email, password, register && Boolean(inviteName)),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível entrar.");
    } finally {
      setBusy(false);
    }
  };

  if (contexts)
    return (
      <Contexts
        contexts={contexts}
        onSelect={(data) => {
          void accept(data).catch((e) => setError(e.message));
        }}
        onLogout={() => {
          void api.logout().then(() => location.replace("/"));
        }}
      />
    );

  return (
    <div
      className="workspace django-workspace login-workspace"
      aria-busy={!ready || busy}
    >
      <main className="main-area">
        <div className="experience-layout">
          <section className="app-screen login-screen" aria-label="Entrar">
            <fieldset
              disabled={!ready || busy}
              style={{ border: 0, padding: 0, minWidth: 0 }}
            >
              <LoginPage
                real
                canRegister={Boolean(invite && inviteName)}
                inviteName={inviteName}
                loginSubmit={loginSubmit}
                navigate={() => {}}
              />
            </fieldset>
            {error && (
              <p role="alert" style={{ padding: "0 24px 24px" }}>
                {error}
              </p>
            )}
            {!ready && <p role="status">Conectando…</p>}
          </section>
        </div>
      </main>
    </div>
  );
}
