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
    phone: string;
    description: string;
    active: boolean;
    draft: Record<string, string>;
    accessUser?: {
      id: string;
      email: string;
      firstName: string;
      lastName: string;
      passwordConfigured: boolean;
    } | null;
  }[];
  events: {
    id: string;
    name: string;
    state: string;
    status: string;
    organization: string;
    organizationId: string;
  }[];
  activity: { id: string; action: string; created: string }[];
  alerts: { id: string; title: string; body: string }[];
};
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
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [formKind, setFormKind] = useState<
    "client-create" | "client-edit" | "event-create"
  >("client-create");
  const [pendingPage, setPendingPage] = useState<string | null>(null);
  const selectedClient = data?.clients.find(
    (client) => client.id === selectedClientId,
  );
  const navigate = (next: string) => {
    if (wizard && dirty) {
      setExit(true);
      setPendingPage(next);
      return;
    }
    setPage(next);
    setSearch("");
    setWizard(false);
    setSelectedClientId(null);
    setError("");
  };
  const [wizard, setWizard] = useState(false),
    [draft, setDraft] = useState<Record<string, string>>({}),
    [dirty, setDirty] = useState(false),
    [busy, setBusy] = useState(false),
    [exit, setExit] = useState(false);
  const begin = (
    kind: typeof formKind,
    values: Record<string, string> = {},
  ) => {
    setFormKind(kind);
    setDraft(values);
    setDirty(false);
    setError("");
    setWizard(true);
    setPendingPage(null);
  };
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
  function field(key: string, label: string, type = "text", required = true) {
    return (
      <label>
        {label}
        <input
          required={required}
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
        action:
          formKind === "event-create"
            ? "create_event"
            : formKind === "client-edit"
              ? "update_client"
              : "create_client",
        ...(formKind === "event-create"
          ? {
              starts: new Date(draft.starts).toISOString(),
              ends: new Date(draft.ends).toISOString(),
            }
          : {}),
      };
      const result = await request<{ id: string }>("global/", "POST", body);
      setDraft({ ...draft, id: result.id });
      setDirty(false);
      setWizard(false);
      setPage(formKind === "event-create" ? "Eventos" : "Clientes");
      setSearch("");
      setClientFilter("Todos");
      setEventFilter("Todos");
      setSelectedClientId(formKind === "event-create" ? null : result.id);
      await load();
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
          {!wizard &&
            !selectedClientId &&
            ["Clientes", "Eventos"].includes(page) && (
              <button
                className="adm-primary"
                onClick={() =>
                  begin(page === "Eventos" ? "event-create" : "client-create")
                }
              >
                {page === "Eventos" ? "+ Novo evento" : "+ Novo cliente"}
              </button>
            )}
          {wizard ? (
            <form onSubmit={save}>
              <h2>
                {formKind === "event-create"
                  ? "Novo evento"
                  : formKind === "client-edit"
                    ? "Completar cadastro do cliente"
                    : "Novo cliente"}
              </h2>
              <fieldset disabled={busy} className="global-form-fields">
                {formKind !== "event-create" && (
                  <>
                    {field("contact", "Nome")}
                    {field("email", "E-mail", "email")}
                    {field("phone", "Telefone", "tel")}
                  </>
                )}
                {formKind === "client-edit" && (
                  <>
                    {field("contact_role", "Cargo / função", "text", false)}
                    <label>
                      Observações
                      <textarea
                        maxLength={4000}
                        value={draft.notes || ""}
                        onChange={(e) => {
                          setDraft({ ...draft, notes: e.target.value });
                          setDirty(true);
                        }}
                      />
                    </label>
                    <h3>Dados da organização</h3>
                    {field(
                      "organization",
                      "Nome da organização",
                      "text",
                      false,
                    )}
                    <label>
                      Descrição da organização
                      <textarea
                        maxLength={4000}
                        value={draft.description || ""}
                        onChange={(e) => {
                          setDraft({ ...draft, description: e.target.value });
                          setDirty(true);
                        }}
                      />
                    </label>
                  </>
                )}
                {formKind === "event-create" && (
                  <>
                    <label>
                      Cliente
                      <select
                        aria-label="Cliente"
                        required
                        value={draft.client || ""}
                        onChange={(e) => {
                          setDraft({ ...draft, client: e.target.value });
                          setDirty(true);
                        }}
                      >
                        <option value="">Selecione um cliente</option>
                        {data?.clients
                          .filter((client) => client.active)
                          .map((client) => (
                            <option key={client.id} value={client.id}>
                              {client.contact || client.name}
                              {client.contact && client.name !== client.contact
                                ? ` — ${client.name}`
                                : ""}
                            </option>
                          ))}
                      </select>
                    </label>
                    {field("event", "Nome do evento")}
                    {field("starts", "Início", "datetime-local")}
                    {field("ends", "Término", "datetime-local")}
                    {field(
                      "responsible",
                      "E-mail da conta responsável",
                      "email",
                    )}
                    <p>
                      Informe o e-mail da conta de acesso do responsável. O
                      evento será criado como agendado.
                    </p>
                  </>
                )}
                <div className="adm-actions">
                  <button
                    type="button"
                    onClick={() => (dirty ? setExit(true) : setWizard(false))}
                  >
                    Cancelar
                  </button>
                  <button className="adm-primary" disabled={busy}>
                    {busy
                      ? "Salvando…"
                      : formKind === "event-create"
                        ? "Criar evento"
                        : formKind === "client-edit"
                          ? "Salvar alterações"
                          : "Cadastrar cliente"}
                  </button>
                </div>
              </fieldset>
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
                      onClick={() => begin("client-create")}
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
              {page === "Clientes" && selectedClient && (
                <>
                  <button
                    className="adm-back"
                    onClick={() => setSelectedClientId(null)}
                  >
                    ← Voltar aos clientes
                  </button>
                  <h2>{selectedClient.contact || selectedClient.name}</h2>
                  <section className="adm-card">
                    <h3>Dados do cliente</h3>
                    <dl className="client-details">
                      <dt>Nome</dt>
                      <dd>{selectedClient.contact || selectedClient.name}</dd>
                      <dt>E-mail</dt>
                      <dd>{selectedClient.email || "Não informado"}</dd>
                      <dt>Telefone</dt>
                      <dd>
                        {selectedClient.phone ||
                          selectedClient.draft.phone ||
                          "Não informado"}
                      </dd>
                      <dt>Cargo / função</dt>
                      <dd>
                        {selectedClient.draft.contact_role || "Não informado"}
                      </dd>
                      <dt>Observações</dt>
                      <dd>{selectedClient.draft.notes || "Não informado"}</dd>
                    </dl>
                    <h3>Organização</h3>
                    <p>
                      {selectedClient.draft.organization ||
                        (selectedClient.name !== selectedClient.contact
                          ? selectedClient.name
                          : "Dados da organização ainda não preenchidos.")}
                    </p>
                    {selectedClient.description && (
                      <p>{selectedClient.description}</p>
                    )}
                    <button
                      className="adm-primary"
                      onClick={() =>
                        begin("client-edit", {
                          id: selectedClient.id,
                          contact: selectedClient.contact,
                          email: selectedClient.email,
                          phone:
                            selectedClient.phone ||
                            selectedClient.draft.phone ||
                            "",
                          contact_role: selectedClient.draft.contact_role || "",
                          notes: selectedClient.draft.notes || "",
                          organization:
                            selectedClient.draft.organization ||
                            (selectedClient.name !== selectedClient.contact
                              ? selectedClient.name
                              : ""),
                          description: selectedClient.description || "",
                        })
                      }
                    >
                      Completar / editar cadastro
                    </button>
                  </section>
                  {selectedClient.accessUser && (
                    <section className="adm-card">
                      <h3>Acesso ao sistema</h3>
                      <p>{selectedClient.accessUser.email}</p>
                      <p>
                        {selectedClient.accessUser.firstName}{" "}
                        {selectedClient.accessUser.lastName}
                      </p>
                      {!selectedClient.accessUser.passwordConfigured && (
                        <p>
                          Defina a senha no Django Admin para habilitar o login.
                        </p>
                      )}
                      <a
                        href={`/admin/accounts/user/${selectedClient.accessUser.id}/password/`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {selectedClient.accessUser.passwordConfigured
                          ? "Alterar senha no Django Admin"
                          : "Definir senha no Django Admin"}
                      </a>
                    </section>
                  )}
                  <section className="adm-card">
                    <h3>Eventos do cliente</h3>
                    {data?.events
                      .filter(
                        (event) => event.organizationId === selectedClient.id,
                      )
                      .map((event) => (
                        <p key={event.id}>
                          {event.name} · {event.status}
                        </p>
                      ))}
                    {!data?.events.some(
                      (event) => event.organizationId === selectedClient.id,
                    ) && <p>Nenhum evento cadastrado.</p>}
                    <button
                      onClick={() =>
                        begin("event-create", {
                          client: selectedClient.id,
                          responsible: selectedClient.accessUser?.email || "",
                        })
                      }
                    >
                      + Novo evento
                    </button>
                  </section>
                </>
              )}
              {page === "Clientes" && !selectedClientId && (
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
                        <button
                          onClick={() => {
                            setSelectedClientId(c.id);
                            setError("");
                          }}
                        >
                          Ver cliente
                        </button>
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
              <button
                onClick={() => {
                  setExit(false);
                  setPendingPage(null);
                }}
              >
                Continuar editando
              </button>
              <button
                onClick={() => {
                  setWizard(false);
                  setDirty(false);
                  setExit(false);
                  if (pendingPage) {
                    setPage(pendingPage);
                    setSelectedClientId(null);
                    setSearch("");
                  }
                  setPendingPage(null);
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
