import { useEffect, useState, type FormEvent } from "react";
import Dropdown from "react-bootstrap/Dropdown";
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
    team: { id: string; email: string; firstName: string; lastName: string; role: string; active: boolean; passwordConfigured: boolean }[];
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
const eventStatuses = [
  ["Todos", "Todos"],
  ["DRAFT", "Rascunhos / solicitados"],
  ["RUNNING", "Em andamento"],
  ["SCHEDULED", "Agendados"],
  ["OPEN", "Abertos"],
  ["PAUSED", "Pausados"],
  ["CLOSED", "Encerrados"],
  ["ARCHIVED", "Arquivados"],
] as const;
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
    "client-create" | "client-edit" | "event-create" | "team-create" | "team-edit"
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
          step={type === "number" ? "any" : undefined}
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
            : formKind === "team-create"
              ? "create_team_member"
            : formKind === "team-edit"
              ? "update_team_member"
            : formKind === "client-edit"
              ? "update_client"
              : "create_client",
        ...(formKind === "event-create"
          ? {
              starts: new Date(draft.starts).toISOString(),
              ends: new Date(draft.ends).toISOString(),
              location_interval_minutes:
                draft.location_interval_minutes || "15",
              radius_m: draft.radius_m || "100",
              tolerance_m: draft.tolerance_m || "1000",
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
      setSelectedClientId(formKind === "event-create" ? null : (formKind === "team-create" || formKind === "team-edit") ? draft.client : result.id);
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
                  : formKind === "team-edit"
                    ? "Editar membro da equipe"
                  : formKind === "team-create"
                    ? "Cadastrar membro da equipe"
                  : formKind === "client-edit"
                    ? "Completar cadastro do cliente"
                    : "Novo cliente"}
              </h2>
              <fieldset disabled={busy} className="global-form-fields">
                {formKind !== "event-create" && (
                  <>
                    {field("contact", "Nome")}
                    {field("email", "E-mail", "email")}
                    {!formKind.startsWith("team-") && field("phone", "Telefone", "tel")}
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
                {formKind.startsWith("team-") && (
                  <label>
                    Perfil de acesso
                    <select value={draft.role || "OPERATOR"} onChange={(e) => {
                      setDraft({ ...draft, role: e.target.value });
                      setDirty(true);
                    }}>
                      <option value="OPERATOR">Operador</option>
                      <option value="MODERATOR">Moderador</option>
                      <option value="ADMIN">Responsável pelo evento</option>
                    </select>
                  </label>
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
                          setDraft({ ...draft, client: e.target.value, responsible: "" });
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
                    <label>
                      Descrição
                      <textarea
                        maxLength={4000}
                        value={draft.description || ""}
                        onChange={(e) => {
                          setDraft({ ...draft, description: e.target.value });
                          setDirty(true);
                        }}
                      />
                    </label>
                    <label>
                      Modalidade
                      <select
                        value={draft.mode || "PHYSICAL"}
                        onChange={(e) => {
                          setDirty(true);
                          setDraft({
                            ...draft,
                            mode: e.target.value,
                            auto_activate_participants: "false",
                          });
                        }}
                      >
                        <option value="ONLINE">Online</option>
                        <option value="PHYSICAL">Presencial</option>
                        <option value="HYBRID">Híbrido</option>
                      </select>
                    </label>
                    {draft.mode === "ONLINE" ? (
                      <label>
                        <input
                          type="checkbox"
                          role="switch"
                          className="app-toggle"
                          checked={draft.auto_activate_participants === "true"}
                          onChange={(e) => {
                            setDirty(true);
                            setDraft({
                              ...draft,
                              auto_activate_participants: String(
                                e.target.checked,
                              ),
                            });
                          }}
                        />
                        Ativar automaticamente ao completar o perfil
                        <p>
                          Exige três fotos públicas, uma principal, bio e campos
                          obrigatórios e termos. Dispensa foto de outfit e
                          aprovação da organização.
                        </p>
                      </label>
                    ) : (
                      <>
                        {field("latitude", "Latitude", "number")}
                        {field("longitude", "Longitude", "number")}
                        {field("radius_m", "Raio (metros)", "number", false)}
                        {field(
                          "tolerance_m",
                          "Limite adicional (metros)",
                          "number",
                          false,
                        )}
                      </>
                    )}
                    {field(
                      "location_interval_minutes",
                      "Intervalo de localização (minutos)",
                      "number",
                      false,
                    )}
                    {draft.mode === "ONLINE" && (
                      <p>
                        Após esse intervalo sem interação com o servidor, o
                        participante será considerado ausente. O padrão é 15
                        minutos.
                      </p>
                    )}
                    {field("starts", "Início", "datetime-local")}
                    {field("ends", "Término", "datetime-local")}
                    <label>
                      E-mail da conta responsável
                      <select required value={draft.responsible || ""} onChange={(e) => {
                        setDraft({ ...draft, responsible: e.target.value });
                        setDirty(true);
                      }}>
                        <option value="">Selecione um membro da equipe</option>
                        {data?.clients.find((client) => client.id === draft.client)?.team
                          .filter((member) => member.active)
                          .map((member) => (
                            <option key={member.id} value={member.email}>
                              {member.firstName} {member.lastName} — {member.email}
                            </option>
                          ))}
                      </select>
                    </label>
                    <p>
                      Selecione um membro vinculado ao cliente. O
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
                        : formKind === "team-edit"
                          ? "Salvar altera??es"
                        : formKind === "team-create"
                          ? "Cadastrar membro"
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
                      ["DRAFT", "Eventos solicitados"],
                      ["critical", "Denúncias críticas"],
                      ["pending", "Ocorrências que exigem atenção"],
                    ].map(([k, label]) => (
                      <section className="adm-card" key={k}>
                        {["RUNNING", "SCHEDULED", "PAUSED", "DRAFT"].includes(
                          k,
                        ) ? (
                          <button
                            className="global-event-stat"
                            onClick={() => {
                              navigate("Eventos");
                              setEventFilter(k);
                            }}
                          >
                            <strong>{data?.metrics[k] || 0}</strong>
                            <span>{label}</span>
                          </button>
                        ) : (
                          <>
                            <strong>{data?.metrics[k] || 0}</strong>
                            <p>{label}</p>
                          </>
                        )}
                      </section>
                    ))}
                  </div>
                  <section className="adm-card">
                    <h2>Ações rápidas</h2>
                    <div className="adm-actions">
                    <button
                      className="adm-primary"
                      onClick={() => begin("client-create")}
                    >
                      + Novo cliente
                    </button>
                    <button
                      className="adm-primary"
                      onClick={() => begin("event-create")}
                    >
                      + Novo evento
                    </button>
                    </div>
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
                    <div className="adm-actions">
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
                    {selectedClient.accessUser && (
                      <a className="client-password-button" href={`/admin/accounts/user/${selectedClient.accessUser.id}/password/`} target="_blank" rel="noreferrer">
                        {selectedClient.accessUser.passwordConfigured ? "Alterar senha" : "Definir senha"}
                      </a>
                    )}
                    </div>
                  </section>
                  <section className="adm-card">
                    <div className="client-team-header">
                      <h3>Equipe</h3>
                      <button className="adm-primary" onClick={() => begin("team-create", { client: selectedClient.id, role: "OPERATOR" })}>
                        + Cadastrar membro
                      </button>
                    </div>
                    {selectedClient.team.map((member) => (
                      <div className="client-team-card" key={member.id}>
                        <button className="client-team-edit" onClick={() => begin("team-edit", {
                          client: selectedClient.id,
                          user: member.id,
                          contact: `${member.firstName} ${member.lastName}`.trim(),
                          email: member.email,
                          role: member.role,
                        })} aria-label={`Editar ${member.firstName} ${member.lastName}`}>
                          <strong>{member.firstName.toLocaleUpperCase("pt-BR")}</strong>
                          <span>{member.role === "ADMIN" ? "Respons?vel pelo evento" : member.role === "MODERATOR" ? "Moderador" : "Operador"}{!member.active && " ? Inativo"}</span>
                        </button>
                        <a className="client-password-button" href={`/admin/accounts/user/${member.id}/password/`} target="_blank" rel="noreferrer" aria-label={`Redefinir senha de ${member.firstName} ${member.lastName}`}>
                          Redefinir senha
                        </a>
                      </div>
                    ))}
                    {!selectedClient.team.length && <p>Nenhum membro cadastrado.</p>}
                  </section>
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
                      <Dropdown
                        className="event-status-filter"
                        onSelect={(key) => {
                          if (key) setEventFilter(key);
                        }}
                      >
                        <Dropdown.Toggle
                          id="event-status-filter"
                          variant="primary"
                          aria-label="Situação dos eventos"
                        >
                          {eventStatuses.find(
                            ([key]) => key === eventFilter,
                          )?.[1] || "Todos"}
                        </Dropdown.Toggle>
                        <Dropdown.Menu
                          role="menu"
                          aria-label="Status disponíveis"
                        >
                          {eventStatuses.map(([key, label]) => (
                            <Dropdown.Item
                              key={key}
                              eventKey={key}
                              active={eventFilter === key}
                              role="menuitemradio"
                              aria-checked={eventFilter === key}
                            >
                              {label}
                            </Dropdown.Item>
                          ))}
                        </Dropdown.Menu>
                      </Dropdown>
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
            <div
              className="modal-backdrop"
              onClick={(e) => {
                if (e.target === e.currentTarget) {
                  setExit(false);
                  setPendingPage(null);
                }
              }}
            >
              <section
                className="global-popup"
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
            </div>
          )}
          {decision && (
            <div
              className="modal-backdrop"
              onClick={(e) => {
                if (e.target === e.currentTarget) setDecision(null);
              }}
            >
              <section
                className="global-popup"
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
            </div>
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
