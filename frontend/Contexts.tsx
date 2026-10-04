import { useEffect, useState } from "react";
import { request } from "./backend-client";
import type { SessionData, Context } from "./types";

export function Contexts({
  contexts,
  onSelect,
  onLogout,
}: {
  contexts: Context[];
  onSelect: (d: SessionData) => void;
  onLogout: () => void;
}) {
  const [error, setError] = useState("");
  return (
    <main className="adm-loading">
      <h1>Onde você deseja entrar?</h1>
      {contexts.map((c) => (
        <section className="adm-card" key={c.key}>
          <h2>{c.name}</h2>
          <button
            onClick={() => {
              void request<SessionData>("contexts/", "POST", { key: c.key })
                .then(onSelect)
                .catch((e) => setError(e.message));
            }}
          >
            {c.navigation === "participant"
              ? "Participar"
              : c.navigation === "administration"
                ? "Administrar"
                : "Acessar"}
          </button>
        </section>
      ))}
      {error && <p role="alert">{error}</p>}
      <button onClick={onLogout}>Sair</button>
    </main>
  );
}
