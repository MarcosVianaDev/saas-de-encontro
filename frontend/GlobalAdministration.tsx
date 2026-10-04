import { useEffect, useState, type FormEvent } from "react";
import { request } from "./backend-client";
import type { SessionData } from "./types";
import "./administration.css";
import { AdminNavigation } from "./AdminNavigation";

type GlobalData = {
  staff: boolean;
  metrics: Record<string, number>;
  safety: {
    id: string;
    email: string;
    recurring: boolean;
    reports: number;
    events: { id: string; name: string }[];
  }[];
  clients: {
    id: string;
    name: string;
    contact: string;
    email: string;
    active: boolean;
    draft: Record<string, string>;
  }[];
  events: {
    id: string;
    name: string;
    state: string;
    status: string;
    organization: string;
  }[];
  activity: { id: string; action: string; created: string }[];
  alerts: { id: string; title: string; body: string }[];
};
const steps = [
  "Contato",
  "Organização",
  "Evento",
  "Responsáveis",
  "Revisão",
  "Ativação",
];
export function GlobalAdministration({
  onSelect,
  onLogout,
}: {
  onSelect: (data: SessionData) => void;
  onLogout: () => Promise<void>;
}) {
  const [data, setData] = useState<GlobalData | null>(null),
    [page, setPage] = useState("Início"),
    [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [clientFilter, setClientFilter] = useState("Todos");
  const [eventFilter, setEventFilter] = useState("Todos");
  const navigate = (next: string) => {
    if (wizard && dirty) {
      setExit(true);
      return;
    }
    setPage(next);
    setSearch("");
    setWizard(false);
  };
  const [wizard, setWizard] = useState(false),
    [step, setStep] = useState(0),
    [draft, setDraft] = useState<Record<string, string>>({}),
    [dirty, setDirty] = useState(false),
    [busy, setBusy] = useState(false),
    [exit, setExit] = useState(false);
  const [decision, setDecision] = useState<{
      profile: string;
      action: string;
      marked?: boolean;
      event?: string;
    } | null>(null),
    [reason, setReason] = useState("");
  const load = () =>
    request<GlobalData>("global/")
      .then(setData)
      .catch((e) => setError(e.message));
  useEffect(() => {
    void load();
  }, []);
  useEffect(() => {
    const before = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", before);
    return () => window.removeEventListener("beforeunload", before);
  }, [dirty]);
  function field(key: string, label: string, type = "text") {
    return (
      <label>
        {label}
        <input
          required
          type={type}
          value={
            type === "datetime-local" && draft[key] && draft[key].length > 16
              ? new Date(
                  new Date(draft[key]).getTime() -
                    new Date().getTimezoneOffset() * 60000,
                )
                  .toISOString()
                  .slice(0, 16)
              : draft[key] || ""
          }
          onChange={(e) => {
            setDraft({ ...draft, [key]: e.target.value });
            setDirty(true);
          }}
        />
      </label>
    );
  }
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const body = {
        ...draft,
        starts: draft.starts ? new Date(draft.starts).toISOString() : undefined,
        ends: draft.ends ? new Date(draft.ends).toISOString() : undefined,
        activate: step === 5,
      };
      const result = await request<{ id: string }>("global/", "POST", body);
      setDraft({ ...draft, id: result.id });
      setDirty(false);
      if (step === 5) {
        setWizard(false);
        void load();
      } else setStep(step + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível salvar.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="adm-workspace global-administration">
      <div className="adm-main">
        <header className="adm-topbar">
          <div>
            <small>VISÃO GERAL DO SISTEMA</small>
            <h1>Administração Global</h1>
          </div>
        </header>
        <main className="global-content">
          {error && <p role="alert">{error}</p>}
          {!wizard && !["Mais", "Início"].includes(page) && (
            <button
              className="adm-primary"
              onClick={() => {
                setWizard(true);
                setStep(0);
                setDraft({});
              }}
            >
              + Novo cliente
            </button>
          )}
          {wizard ? (
            <form onSubmit={save}>
              <h2>
                {steps[step]} — {step + 1} de 6
              </h2>
              {step === 0 && (
                <>
                  {field("contact", "Nome do contato")}
                  {field("email", "E-mail", "email")}
                  {field("phone", "Telefone", "tel")}
                </>
              )}
              {step === 1 && field("organization", "Nome da organização")}
              {step === 2 && (
                <>
                  {field("event", "Nome do evento")}
                  {field("starts", "Início", "datetime-local")}
                  {field("ends", "Término", "datetime-local")}
                </>
              )}
              {step === 3 &&
                field("responsible", "E-mail da conta responsável", "email")}
              {step >= 4 && (
                <dl>
                  {Object.entries(draft)
                    .filter(([k]) => k !== "id")
                    .map(([key, value]) => (
                      <div key={key}>
                        <dt>{key}</dt>
                        <dd>{value}</dd>
                      </div>
                    ))}
                </dl>
              )}
              {step === 5 && (
                <p>
                  A ativação cria o evento agendado e vincula a conta
                  responsável existente.
                </p>
              )}
              <div className="adm-actions">
                <button
                  type="button"
                  onClick={() => (step ? setStep(step - 1) : setExit(true))}
                >
                  Voltar
                </button>
                <button className="adm-primary" disabled={busy}>
                  {step === 5
                    ? "Ativar cliente e evento"
                    : "Salvar e continuar"}
                </button>
              </div>
            </form>
          ) : (
            <>
              {page === "Início" && (
                <>
                  <h2>Visão geral</h2>
                  <div className="adm-stats">
                    {[
                      ["RUNNING", "Eventos em andamento"],
                      ["SCHEDULED", "Eventos agendados"],
                      ["PAUSED", "Eventos pausados"],
                      ["critical", "Denúncias críticas"],
                      ["clients", "Clientes ativos"],
                      ["pending", "Ocorrências que exigem atenção"],
                    ].map(([k, label]) => (
                      <section className="adm-card" key={k}>
                        <strong>{data?.metrics[k] || 0}</strong>
                        <p>{label}</p>
                      </section>
                    ))}
                  </div>
                  <section className="adm-card">
                    <h2>Ações rápidas</h2>
                    <button
                      className="adm-primary"
                      onClick={() => {
                        setWizard(true);
                        setStep(0);
                        setDraft({});
                      }}
                    >
                      + Novo cliente
                    </button>
                  </section>
                  <h2>Alertas do sistema</h2>
                  {data?.alerts.map((n) => (
                    <article key={n.id}>
                      <h3>{n.title}</h3>
                      <p>{n.body}</p>
                    </article>
                  ))}
                  <h2>Atividade administrativa</h2>
                  {data?.activity.map((a) => (
                    <p key={a.id}>
                      {a.action} · {new Date(a.created).toLocaleString("pt-BR")}
                    </p>
                  ))}
                </>
              )}
              {page === "Clientes" && (
                <>
                  <h2>Clientes</h2>
                  <div className="global-list-tools">
                    <input
                      type="search"
                      aria-label="Buscar organização ou contato"
                      placeholder="Buscar organização ou contato"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                    />
                    <div
                      className="adm-tabs"
                      aria-label="Situação dos clientes"
                    >
                      {["Todos", "Ativos", "Inativos"].map((filter) => (
                        <button
                          key={filter}
                          className={clientFilter === filter ? "selected" : ""}
                          aria-pressed={clientFilter === filter}
                          onClick={() => setClientFilter(filter)}
                        >
                          {filter}
                        </button>
                      ))}
                    </div>
                  </div>
                  {data?.clients
                    .filter(
                      (c) =>
                        `${c.name} ${c.contact} ${c.email}`
                          .toLocaleLowerCase("pt-BR")
                          .includes(search.toLocaleLowerCase("pt-BR")) &&
                        (clientFilter === "Todos" ||
                          c.active === (clientFilter === "Ativos")),
                    )
                    .map((c) => (
                      <section key={c.id} className="adm-card">
                        <span
                          className={`adm-badge ${c.active ? "positive" : ""}`}
                        >
                          {c.active ? "Ativo" : "Inativo"}
                        </span>
                        <h3>{c.name}</h3>
                        <p>
                          {c.contact} · {c.email}
                        </p>
                        {!c.active && (
                          <button
                            onClick={() => {
                              setDraft({ ...c.draft, id: c.id });
                              setWizard(true);
                              setStep(0);
                            }}
                          >
                            Continuar cadastro
                          </button>
                        )}
                      </section>
                    ))}
                </>
              )}
              {["Eventos", "Início"].includes(page) && (
                <>
                  <h2>{page === "Início" ? "Eventos recentes" : "Eventos"}</h2>
                  {page === "Eventos" && (
                    <div className="global-list-tools">
                      <input
                        type="search"
                        aria-label="Buscar evento ou organização"
                        placeholder="Buscar evento ou organização"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                      />
                      <div
                        className="adm-tabs"
                        aria-label="Situação dos eventos"
                      >
                        {[
                          ["Todos", "Todos"],
                          ["RUNNING", "Em andamento"],
                          ["SCHEDULED", "Agendados"],
                          ["CLOSED", "Encerrados"],
                        ].map(([key, label]) => (
                          <button
                            key={key}
                            className={eventFilter === key ? "selected" : ""}
                            aria-pressed={eventFilter === key}
                            onClick={() => setEventFilter(key)}
                          >
                            {label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                  {data?.events
                    .filter(
                      (e) =>
                        page === "Início" ||
                        (`${e.name} ${e.organization}`
                          .toLocaleLowerCase("pt-BR")
                          .includes(search.toLocaleLowerCase("pt-BR")) &&
                          (eventFilter === "Todos" || e.state === eventFilter)),
                    )
                    .map((e) => (
                      <section key={e.id} className="adm-card">
                        <h3>{e.name}</h3>
                        <p>
                          {e.organization} · {e.status}
                        </p>
                        <button
                          onClick={() =>
                            void request<SessionData>("global/event/", "POST", {
                              event: e.id,
                            })
                              .then(onSelect)
                              .catch((e) => setError(e.message))
                          }
                        >
                          Administrar evento
                        </button>
                      </section>
                    ))}
                </>
              )}
              {page === "Mais" && (
                <>
                  <h1>Mais</h1>
                  <section
                    className="adm-card account-options"
                    aria-label="Conta"
                  >
                    <h2>Conta</h2>
                    <button
                      className="account-logout"
                      disabled={busy}
                      onClick={async () => {
                        setBusy(true);
                        setError("");
                        try {
                          await onLogout();
                        } catch (e) {
                          setError(
                            e instanceof Error
                              ? e.message
                              : "Não foi possível sair da conta.",
                          );
                        } finally {
                          setBusy(false);
                        }
                      }}
                    >
                      Sair da conta
                    </button>
                  </section>
                  <h2>Acompanhamento de segurança</h2>
                  <p>
                    A marcação de recorrência não bloqueia o ingresso em outros
                    eventos. A comunicação à organização local depende de uma
                    decisão da gestão global.
                  </p>
                  {data?.safety.map((p) => (
                    <article key={p.id}>
                      <h3>{p.email}</h3>
                      <p>
                        {p.reports} denúncias relevantes ·{" "}
                        {p.recurring
                          ? "Denunciado recorrente"
                          : "Sem marcação de recorrência"}
                      </p>
                      <button
                        onClick={() => {
                          setReason("");
                          setDecision({
                            profile: p.id,
                            action: "recurrence",
                            marked: !p.recurring,
                          });
                        }}
                      >
                        {p.recurring
                          ? "Remover marcação"
                          : "Marcar como denunciado recorrente"}
                      </button>
                      {p.recurring &&
                        p.events.map((e) => (
                          <button
                            key={e.id}
                            onClick={() => {
                              setReason("");
                              setDecision({
                                profile: p.id,
                                action: "inform_event",
                                event: e.id,
                              });
                            }}
                          >
                            Comunicar à gestão: {e.name}
                          </button>
                        ))}
                    </article>
                  ))}
                  {data?.staff && (
                    <a href="/admin/" target="_blank" rel="noreferrer">
                      Admin do sistema
                    </a>
                  )}
                </>
              )}
            </>
          )}
          {exit && (
            <section
              role="dialog"
              aria-modal="true"
              aria-label="Alterações não salvas"
            >
              <p>Existem alterações não salvas. Deseja sair mesmo assim?</p>
              <button onClick={() => setExit(false)}>Continuar editando</button>
              <button
                onClick={() => {
                  setWizard(false);
                  setDirty(false);
                  setExit(false);
                }}
              >
                Sair sem salvar
              </button>
            </section>
          )}
          {decision && (
            <section
              role="dialog"
              aria-modal="true"
              aria-label="Confirmar acompanhamento"
            >
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void request("global/", "POST", {
                    ...decision,
                    reason,
                    confirmed: true,
                  })
                    .then(() => {
                      setDecision(null);
                      void load();
                    })
                    .catch((e) => setError(e.message));
                }}
              >
                <h2>Confirmar decisão de acompanhamento?</h2>
                <label>
                  Motivo
                  <textarea
                    required
                    maxLength={4000}
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </label>
                <button type="button" onClick={() => setDecision(null)}>
                  Cancelar
                </button>
                <button>Confirmar decisão</button>
              </form>
            </section>
          )}
        </main>
      </div>
      <AdminNavigation
        label="Navegação da administração global"
        current={page}
        disabled={busy}
        items={[
          { key: "Início", label: "Início", icon: "home" },
          { key: "Clientes", label: "Clientes", icon: "people" },
          { key: "Eventos", label: "Eventos", icon: "calendar" },
          { key: "Mais", label: "Mais", icon: "more" },
        ]}
        onSelect={navigate}
      />
    </div>
  );
}
