import { CachedImage } from "./CachedImage";
import { useEffect, useRef, useState, type FormEvent } from "react";
import QRCode from "qrcode";
import { closeDialogOnBackdrop } from "./modal-backdrop";
import { request } from "./backend-client";
import { adminMock } from "./administration-mock";
import "./administration.css";
import { AdminNavigation, type AdminNavItem } from "./AdminNavigation";
import { EventOperations } from "./EventOperations";
import { EventConfiguration } from "./EventConfiguration";
import { TeamManagement } from "./TeamManagement";
import {
  ParticipantOperation,
  PassManagement,
  FinancialReport,
  Announcements,
  ProfileIntervention,
} from "./AdminOperations";
import { SupportPanel, NotificationCenter } from "./ParticipantExtras";

export type Participant = {
  id: string;
  name: string;
  age: number | null;
  job: string;
  email: string;
  image: string;
  status: string;
  reason: string;
  created: string;
  updated: string;
  lastSeen: string | null;
  online: boolean;
  presence?: string;
  reports: number | null;
  blocks: number | null;
};
type Entry = { id: string; author: string; body: string; created: string };
export type Case = {
  id: string;
  reference: string;
  reason: string;
  reported: Participant;
  description: string;
  kind: string;
  priority: number;
  unfounded?: boolean;
  reporter: Participant | null;
  author: string;
  status: string;
  created: string;
  closed: string | null;
  responsible: string | null;
  notes: Entry[];
  history: Entry[];
  evidence: {
    id: string;
    description: string;
    content: string | null;
    snapshot?: { body?: string; photoChanged?: boolean };
  }[];
};
export type AdminData = {
  permissions?: string[];
  globalContext?: boolean;
  role: string;
  events: { id: string; name: string; role: string }[];
  event: {
    state?: string;
    mode?: string;
    id: string;
    name: string;
    description: string;
    starts: string | null;
    ends: string | null;
    status: string;
    joinPath: string | null;
    responsible: string[];
  };
  participants: Participant[];
  cases: Case[];
  blockSignals: { participant: Participant; timeline: string[] }[];
  metrics: {
    participants: number;
    active: number;
    new: number;
    matches: number;
    conversations: number;
    blocks: number | null;
  };
  team: { id: string; name: string; role: string }[];
};
type Page =
  | "dashboard"
  | "participants"
  | "moderation"
  | "event"
  | "more"
  | "qr"
  | "team"
  | "report";
const date = (value: string | null) =>
  value ? new Date(value).toLocaleString("pt-BR") : "Não definido";
const roleLabels: Record<string, string> = {
  ADMIN: "Administrador",
  MODERATOR: "Moderador",
  OPERATOR: "Operador",
};
const pages: [Page, string, string][] = [
  ["dashboard", "Dashboard", "⌂"],
  ["participants", "Participantes", "♧"],
  ["moderation", "Moderação", "♢"],
  ["event", "Evento", "▦"],
  ["more", "Mais", "⋯"],
];
function Badge({ children }: { children: string }) {
  return (
    <span
      className={`adm-badge ${children === "Ativo" || children === "Resolvida" || children === "Em andamento" ? "positive" : children === "Banido" || children === "Pendente" || children === "Suspenso" ? "danger" : ""}`}
    >
      {children}
    </span>
  );
}

export function Administration({
  onLogout,
  mock = false,
  onContext,
}: {
  onLogout: () => Promise<void>;
  mock?: boolean;
  onContext?: (global?: boolean) => void;
}) {
  const adminRequest = mock ? adminMock.request : request;
  const [data, setData] = useState<AdminData | null>(null);
  const readPage = (): Page => {
    const value = location.hash.replace("#admin-", "").split("?")[0];
    return [
      "dashboard",
      "participants",
      "moderation",
      "event",
      "more",
      "qr",
      "team",
      "report",
    ].includes(value)
      ? (value as Page)
      : "dashboard";
  };
  const [page, setPage] = useState<Page>(readPage);
  const [personId, setPersonId] = useState<string | null>(
    new URLSearchParams(location.hash.split("?")[1]).get("participant"),
  );
  const [caseId, setCaseId] = useState<string | null>(null);
  const [origin, setOrigin] = useState<{
    caseId?: string;
    personId?: string;
  } | null>(null);
  const [signalId, setSignalId] = useState<string | null>(null);
  const [tab, setTab] = useState("Informações");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("Todos");
  const [recent, setRecent] = useState(false);
  const [moderationFilter, setModerationFilter] = useState("Todos");
  const [order, setOrder] = useState("Nome");
  const [showFilters, setShowFilters] = useState(false);
  const [caseType, setCaseType] = useState("Todos");
  const [caseReason, setCaseReason] = useState("");
  const [casePeriod, setCasePeriod] = useState("Todos");
  const [caseOrder, setCaseOrder] = useState("Mais recentes");
  const [action, setAction] = useState<string | null>(null);
  const [unfounded, setUnfounded] = useState(false);
  const [reason, setReason] = useState("");
  const [selectedReason, setSelectedReason] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [qr, setQr] = useState("");
  const [fullscreen, setFullscreen] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const changed = () => {
      setPage(readPage());
      setPersonId(
        new URLSearchParams(location.hash.split("?")[1]).get("participant"),
      );
      setCaseId(null);
    };
    window.addEventListener("hashchange", changed);
    return () => window.removeEventListener("hashchange", changed);
  }, []);
  const fetchData = async () => {
    const result = await adminRequest<AdminData>("event-admin/");
    setData(result);
  };
  useEffect(() => {
    let disposed = false;
    const refresh = async () => {
      try {
        const result = await adminRequest<AdminData>("event-admin/");
        if (!disposed) setData(result);
      } catch (e) {
        if (!disposed)
          setError(e instanceof Error ? e.message : "Falha ao carregar.");
      }
    };
    void refresh();
    const timer = window.setInterval(() => {
      if (!document.hidden && !dialog.current?.open) void refresh();
    }, 15000);
    return () => {
      disposed = true;
      clearInterval(timer);
    };
  }, []);
  const joinUrl = data?.event.joinPath
    ? new URL(data.event.joinPath, location.origin).href
    : "";
  useEffect(() => {
    let disposed = false;
    setQr("");
    if (joinUrl)
      void QRCode.toDataURL(joinUrl, {
        width: 600,
        margin: 4,
        errorCorrectionLevel: "M",
      })
        .then((url) => {
          if (!disposed) setQr(url);
        })
        .catch(() => setError("Não foi possível gerar o QR Code."));
    return () => {
      disposed = true;
    };
  }, [joinUrl]);
  useEffect(() => {
    if (action) dialog.current?.showModal();
    else dialog.current?.close();
  }, [action]);
  const navigate = (next: Page) => {
    setOrigin(null);
    setSignalId(null);
    setRecent(false);
    setModerationFilter("Todos");
    setCaseType("Todos");
    setCaseReason("");
    setCasePeriod("Todos");
    setPage(next);
    setPersonId(null);
    setCaseId(null);
    setSearch("");
    setStatus("Todos");
    setShowFilters(false);
    setTab("Informações");
    location.hash = `admin-${next}`;
  };
  const run = async (fn: () => Promise<void>) => {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha na operação.");
    } finally {
      setBusy(false);
    }
  };
  const openAction = (next: string) => {
    setReason("");
    setSelectedReason("");
    setConfirmed(false);
    setUnfounded(Boolean(data?.cases.find((c) => c.id === caseId)?.unfounded));
    setAction(next);
  };
  const execute = async (e: FormEvent) => {
    e.preventDefault();
    await run(async () => {
      await adminRequest(
        caseId
          ? `event-admin/cases/${caseId}/action/`
          : `event-admin/participants/${personId}/action/`,
        "POST",
        {
          action,
          reason: [selectedReason, reason].filter(Boolean).join(": "),
          category: action === "report" ? selectedReason : undefined,
          confirmed,
          unfounded: action === "resolve" ? unfounded : undefined,
        },
      );
      await fetchData();
      setAction(null);
      setNotice("Ação registrada com sucesso.");
    });
  };
  if (!data)
    return (
      <main className="adm-loading">
        <h1>Administração do evento</h1>
        <p role="status">{error || "Carregando…"}</p>
        <button onClick={() => void run(fetchData)}>Tentar novamente</button>
        <button onClick={() => void onLogout()}>Sair</button>
      </main>
    );
  const moderate =
    ["ADMIN", "MODERATOR"].includes(data.role) ||
    Boolean(data.permissions?.includes("reports"));
  const person = data.participants.find((p) => p.id === personId);
  const readOnly = ["CLOSED", "ARCHIVED"].includes(data.event.state || "");
  const occurrence = data.cases.find((c) => c.id === caseId);
  const signal = data.blockSignals.find((s) => s.participant.id === signalId);
  const pending = data.cases.filter((c) => c.status !== "Resolvida");
  const filtered = data.participants
    .filter(
      (p) =>
        `${p.name} ${p.email}`
          .toLocaleLowerCase()
          .includes(search.toLocaleLowerCase()) &&
        (status === "Todos" || p.status === status) &&
        (!recent || new Date(p.created).getTime() >= Date.now() - 3600000) &&
        (moderationFilter === "Todos" ||
          (moderationFilter === "Com denúncias" && !!p.reports) ||
          (moderationFilter === "Com bloqueios" && !!p.blocks) ||
          (moderationFilter === "Sem ocorrências" && !p.reports && !p.blocks) ||
          (moderationFilter === "Sob análise" &&
            data.cases.some(
              (c) => c.reported.id === p.id && c.status === "Em análise",
            ))),
    )
    .sort((a, b) =>
      order === "Nome"
        ? a.name.localeCompare(b.name, "pt-BR")
        : new Date(
            order === "Cadastro mais recente"
              ? b.created
              : b.lastSeen || "1970-01-01",
          ).getTime() -
          new Date(
            order === "Cadastro mais recente"
              ? a.created
              : a.lastSeen || "1970-01-01",
          ).getTime(),
    );
  const filteredCases = data.cases.filter(
    (c) =>
      (status === "Todos" || c.status === status) &&
      (caseType === "Todos" || c.kind === caseType) &&
      c.reason.toLocaleLowerCase().includes(caseReason.toLocaleLowerCase()) &&
      (casePeriod === "Todos" ||
        new Date(c.created).getTime() >=
          (casePeriod === "Hoje"
            ? new Date().setHours(0, 0, 0, 0)
            : Date.now() - 7 * 86400000)) &&
      `${c.reason} ${c.reference} ${c.reported.name} ${c.reporter?.name || c.author}`
        .toLocaleLowerCase()
        .includes(search.toLocaleLowerCase()),
  );
  const personRow = (p: Participant) => (
    <button
      className="adm-person"
      key={p.id}
      onClick={() => {
        setOrigin(caseId ? { caseId } : null);
        setPersonId(p.id);
        setCaseId(null);
        setTab("Informações");
      }}
    >
      <CachedImage src={p.image} alt="" />
      <span>
        <strong>
          {p.name}
          {p.age ? `, ${p.age}` : ""}
        </strong>
        <small>{p.job || p.email}</small>
        <small>
          {p.online
            ? "Online agora"
            : p.presence === "ABSENT"
              ? "Ausente"
            : p.lastSeen
              ? `Última atividade: ${date(p.lastSeen)}`
              : "Sem atividade recente"}
        </small>
        <Badge>{p.status}</Badge>
      </span>
      <span aria-hidden="true">›</span>
    </button>
  );
  const caseRow = (c: Case) => (
    <button
      className="adm-case"
      key={c.id}
      onClick={() => {
        setOrigin(personId ? { personId } : null);
        setCaseId(c.id);
        setPersonId(null);
        setTab("Informações");
      }}
    >
      <span className="adm-case-icon" aria-hidden="true">
        !
      </span>
      <span>
        <strong>
          {c.kind} #{c.reference}
        </strong>
        <p>{c.reason}</p>
        <small>
          Denunciado: {c.reported.name}
          <br />
          Por: {c.reporter?.name || c.author} · {date(c.created)}
        </small>
      </span>
      <Badge>{c.status}</Badge>
    </button>
  );
  const stats = (
    <div className="adm-stats">
      {[
        ["Participantes", data.metrics.participants],
        ["Ativos agora", data.metrics.active],
        ["Matches", data.metrics.matches],
        ["Conversas", data.metrics.conversations],
      ].map(([label, value], i) => (
        <button
          key={label}
          className={`adm-stat stat-${i}`}
          onClick={() => navigate(i < 2 ? "participants" : "report")}
        >
          <span>{["♧", "◉", "♡", "▤"][i]}</span>
          <div>
            <strong>{value}</strong>
            <small>{label}</small>
          </div>
        </button>
      ))}
    </div>
  );
  return (
    <div
      className={`adm-workspace ${data.globalContext ? "global-context" : ""}`}
      aria-busy={busy}
    >
      <aside className="adm-sidebar">
        <a
          className="adm-brand"
          href="#admin-dashboard"
          onClick={() => navigate("dashboard")}
        >
          Event<span>Connect</span>
        </a>
        <p>Administração do evento</p>
        {pages
          .filter(([p]) => p !== "moderation" || moderate)
          .map(([p, label, icon]) => (
            <button
              key={p}
              aria-label={label}
              className={page === p ? "selected" : ""}
              onClick={() => navigate(p)}
            >
              <span>{icon}</span>
              {label}
              {p === "moderation" && pending.length > 0 && (
                <b>{pending.length}</b>
              )}
            </button>
          ))}
        <small>{roleLabels[data.role]}</small>
        <button onClick={() => void run(onLogout)}>Sair da conta</button>
      </aside>
      <main className="adm-main">
        {!mock && onContext && (
          <button
            className="adm-back"
            onClick={() => onContext(Boolean(data.globalContext))}
          >
            {data.globalContext
              ? "← Voltar à Administração Global"
              : "Trocar contexto"}
          </button>
        )}
        {!mock && data.role === "DELEGATED" && (
          <button
            onClick={() =>
              void run(async () => {
                await request("event-admin/team/", "POST", {
                  action: "reclaim",
                });
                await fetchData();
              })
            }
          >
            Reassumir administração
          </button>
        )}
        <header className="adm-topbar">
          <div>
            <small>PAINEL DO EVENTO</small>
            <strong>{data.event.name}</strong>
          </div>
          {data.events.length > 1 && (
            <select
              aria-label="Selecionar evento"
              value={data.event.id}
              onChange={(e) =>
                void run(async () => {
                  await adminRequest("event-admin/", "POST", {
                    event: e.target.value,
                  });
                  await fetchData();
                  navigate("dashboard");
                })
              }
            >
              {data.events.map((e) => (
                <option value={e.id} key={e.id}>
                  {e.name}
                </option>
              ))}
            </select>
          )}
          <Badge>{roleLabels[data.role]}</Badge>
        </header>
        {mock && (
          <section
            className="adm-card adm-actions"
            aria-label="Controles da demonstração"
          >
            <span>Prévia administrativa · dados fictícios em memória</span>
            <label>
              Papel de demonstração
              <select
                aria-label="Papel de demonstração"
                value={data.role}
                onChange={(e) =>
                  void run(async () => {
                    adminMock.setRole(e.target.value);
                    await fetchData();
                    navigate("dashboard");
                  })
                }
              >
                {Object.entries(roleLabels).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <button
              onClick={() =>
                void run(async () => {
                  adminMock.reset();
                  await fetchData();
                  navigate("dashboard");
                  setNotice("Demonstração restaurada.");
                })
              }
            >
              Restaurar demonstração
            </button>
            <button
              onClick={() => {
                location.hash = "perfil";
              }}
            >
              Explorar participante
            </button>
          </section>
        )}
        {error && (
          <div className="adm-alert" role="alert">
            {error}
            <button onClick={() => setError("")} aria-label="Fechar erro">
              ×
            </button>
          </div>
        )}
        {notice && (
          <div className="adm-success" role="status">
            {notice}
            <button onClick={() => setNotice("")} aria-label="Fechar aviso">
              ×
            </button>
          </div>
        )}
        {signal ? (
          <>
            <button className="adm-back" onClick={() => setSignalId(null)}>
              ‹ Voltar à moderação
            </button>
            <h1>Bloqueios relacionados</h1>
            <section className="adm-card">
              <h2>{signal.participant.name}</h2>
              <p>{signal.timeline.length} bloqueios recebidos neste evento</p>
              <small>
                Indicadores para análise; não constituem prova nem aplicam
                sanções automaticamente.
              </small>
              <ol className="adm-timeline">
                {signal.timeline.map((t, i) => (
                  <li key={i}>
                    <small>{date(t)}</small>
                    <p>Bloqueio registrado</p>
                  </li>
                ))}
              </ol>
              <button
                onClick={() => {
                  setPersonId(signal.participant.id);
                  setSignalId(null);
                }}
              >
                Ver participante
              </button>
            </section>
          </>
        ) : person ? (
          <>
            <button
              className="adm-back"
              onClick={() => {
                setPersonId(null);
                if (origin?.caseId) {
                  setCaseId(origin.caseId);
                  setTab("Informações");
                }
                setOrigin(null);
              }}
            >
              ‹{" "}
              {origin?.caseId
                ? "Voltar à ocorrência"
                : "Voltar aos participantes"}
            </button>
            <section className="adm-profile">
              <CachedImage src={person.image} alt="" />
              <h1>
                {person.name}
                {person.age ? `, ${person.age}` : ""}
              </h1>
              <p>{person.job}</p>
              <Badge>{person.status}</Badge>
            </section>
            <div className="adm-tabs">
              {["Informações", ...(moderate ? ["Ocorrências"] : [])].map(
                (t) => (
                  <button
                    key={t}
                    className={tab === t ? "selected" : ""}
                    onClick={() => setTab(t)}
                  >
                    {t}
                  </button>
                ),
              )}
            </div>
            {tab === "Informações" ? (
              <section className="adm-card">
                <dl>
                  <dt>Nome completo</dt>
                  <dd>{person.name}</dd>
                  <dt>E-mail</dt>
                  <dd>{person.email}</dd>
                  <dt>ID da participação</dt>
                  <dd>{person.id}</dd>
                  <dt>Cadastro</dt>
                  <dd>{date(person.created)}</dd>
                  <dt>Situação no evento</dt>
                  <dd>{person.status}</dd>
                  {person.reason && (
                    <>
                      <dt>Motivo da restrição</dt>
                      <dd>{person.reason}</dd>
                    </>
                  )}
                </dl>
              </section>
            ) : (
              <>
                <section className="adm-card">
                  <h2>Contexto administrativo</h2>
                  <p>
                    {person.reports} denúncias recebidas · {person.blocks}{" "}
                    bloqueios relacionados
                  </p>
                  <small>
                    Bloqueios são sinais para análise, sem sanção automática.
                  </small>
                </section>
                {data.cases
                  .filter(
                    (c) =>
                      c.reported.id === person.id ||
                      c.reporter?.id === person.id,
                  )
                  .map(caseRow)}
              </>
            )}
            {moderate && !readOnly && (
              <section className="adm-card">
                <h2>Ações administrativas</h2>
                <div className="adm-actions">
                  <button onClick={() => openAction("report")}>
                    Abrir ocorrência
                  </button>
                  {person.status !== "Banido" &&
                    (person.status === "Suspenso" ? (
                      <button onClick={() => openAction("reactivate")}>
                        Reativar participante
                      </button>
                    ) : (
                      <button onClick={() => openAction("suspend")}>
                        Suspender do evento
                      </button>
                    ))}
                  {data.role === "ADMIN" && person.status !== "Banido" && (
                    <button
                      className="adm-danger-button"
                      onClick={() => openAction("ban")}
                    >
                      Remover acesso ao evento
                    </button>
                  )}
                </div>
              </section>
            )}
            {!mock && (
              <ParticipantOperation
                id={person.id}
                gpsEnabled={data.event.mode !== "ONLINE"}
                manager={data.role === "ADMIN"}
                historyAllowed={["PAUSED", "CLOSED", "ARCHIVED"].includes(
                  data.event.state || "",
                )}
                canInvestigate={
                  data.role === "ADMIN" && data.event.state === "PAUSED"
                }
                permissions={readOnly ? [] : data.permissions || []}
                onChanged={() => void fetchData()}
              />
            )}
            {!mock &&
              !readOnly &&
              data.permissions?.some((p) =>
                ["remove_photo", "edit_bio"].includes(p),
              ) && (
                <ProfileIntervention
                  id={person.id}
                  permissions={data.permissions}
                  onChanged={() => void fetchData()}
                />
              )}
            {!mock && data.permissions?.includes("passes") && (
              <PassManagement
                participantId={person.id}
                role={data.role}
                readOnly={readOnly}
              />
            )}
          </>
        ) : occurrence ? (
          <>
            <button
              className="adm-back"
              onClick={() => {
                setCaseId(null);
                if (origin?.personId) {
                  setPersonId(origin.personId);
                  setTab("Ocorrências");
                }
                setOrigin(null);
              }}
            >
              ‹{" "}
              {origin?.personId
                ? "Voltar ao participante"
                : "Voltar às ocorrências"}
            </button>
            <div className="adm-heading">
              <div>
                <h1>Ocorrência #{occurrence.reference}</h1>
                <p>{date(occurrence.created)}</p>
              </div>
              <Badge>{occurrence.status}</Badge>
            </div>
            <section className="adm-card">
              <h2>{occurrence.reason}</h2>
              <small>
                Responsável: {occurrence.responsible || "Não atribuído"}
              </small>
            </section>
            <div className="adm-tabs">
              {["Informações", "Evidências e contexto", "Histórico"].map(
                (t) => (
                  <button
                    key={t}
                    className={tab === t ? "selected" : ""}
                    onClick={() => setTab(t)}
                  >
                    {t}
                  </button>
                ),
              )}
            </div>
            {tab === "Informações" ? (
              <>
                <section className="adm-card">
                  <h2>Envolvidos</h2>
                  <small>Denunciante</small>
                  {occurrence.reporter ? (
                    personRow(occurrence.reporter)
                  ) : (
                    <p>{occurrence.author} · Administração</p>
                  )}
                  <small>Denunciado</small>
                  {personRow(occurrence.reported)}
                  <h2>Relato registrado</h2>
                  <p className="adm-preserve">{occurrence.description}</p>
                </section>
                <section className="adm-card">
                  <h2>Notas internas</h2>
                  {occurrence.notes.length ? (
                    occurrence.notes.map((n) => (
                      <article key={n.id}>
                        <strong>
                          {n.author} · {date(n.created)}
                        </strong>
                        <p className="adm-preserve">{n.body}</p>
                      </article>
                    ))
                  ) : (
                    <p>Nenhuma nota registrada.</p>
                  )}
                  {occurrence.status !== "Resolvida" && (
                    <button onClick={() => openAction("note")}>
                      Adicionar nota
                    </button>
                  )}
                </section>
              </>
            ) : tab === "Histórico" ? (
              <section className="adm-card">
                <h2>Histórico da ocorrência</h2>
                <ol className="adm-timeline">
                  <li>
                    <small>{date(occurrence.created)}</small>
                    <p>Ocorrência registrada</p>
                  </li>
                  {occurrence.history.map((a) => (
                    <li key={a.id}>
                      <small>
                        {date(a.created)} · {a.author}
                      </small>
                      <p className="adm-preserve">{a.body}</p>
                    </li>
                  ))}
                </ol>
              </section>
            ) : (
              <section className="adm-card">
                <h2>Evidências</h2>
                {occurrence.evidence.length ? (
                  occurrence.evidence.map((e) => (
                    <p key={e.id}>
                      {e.description || "Evidência registrada sem descrição"}
                      {e.snapshot?.body && (
                        <blockquote>{e.snapshot.body}</blockquote>
                      )}
                      {e.content && (
                        <>
                          <br />
                          <a href={e.content} target="_blank" rel="noreferrer">
                            Baixar evidência
                          </a>
                        </>
                      )}
                    </p>
                  ))
                ) : (
                  <p>Nenhuma evidência registrada.</p>
                )}
                <h2>Contexto relacionado</h2>
                <p>
                  {occurrence.reported.blocks} bloqueios ·{" "}
                  {occurrence.reported.reports} denúncias neste evento
                </p>
                <small>
                  Esses indicadores não estabelecem culpa automaticamente.
                </small>
              </section>
            )}
            {!readOnly && (
              <section className="adm-card">
                <h2>Decisão e acompanhamento</h2>
                <div className="adm-actions">
                  {occurrence.status === "Resolvida" ? (
                    data.role === "ADMIN" && (
                      <button onClick={() => openAction("reopen")}>
                        Reabrir ocorrência
                      </button>
                    )
                  ) : (
                    <>
                      {!occurrence.responsible && (
                        <button onClick={() => openAction("assume")}>
                          Assumir caso
                        </button>
                      )}
                      <button onClick={() => openAction("resolve")}>
                        Arquivar sem ação
                      </button>
                      <button onClick={() => openAction("suspend")}>
                        Suspender participante
                      </button>
                      {data.role === "ADMIN" && (
                        <button
                          className="adm-danger-button"
                          onClick={() => openAction("ban")}
                        >
                          Banir do evento
                        </button>
                      )}
                    </>
                  )}
                </div>
                <small>
                  Sanções permanecem em acompanhamento até a resolução explícita
                  do caso.
                </small>
              </section>
            )}
          </>
        ) : (
          <>
            {page === "dashboard" && (
              <>
                <section className="adm-hero">
                  <Badge>{data.event.status}</Badge>
                  <h1>{data.event.name}</h1>
                  <p>
                    {date(data.event.starts)} — {date(data.event.ends)}
                  </p>
                  <button onClick={() => navigate("event")}>
                    Ver evento ›
                  </button>
                </section>
                {data.role === "ADMIN" && stats}
                {moderate && (
                  <button
                    className="adm-attention"
                    onClick={() => navigate("moderation")}
                  >
                    <strong>
                      Requer atenção <b>{pending.length}</b>
                    </strong>
                    <p>
                      {pending.filter((c) => c.status === "Pendente").length}{" "}
                      pendentes ·{" "}
                      {pending.filter((c) => c.status === "Em análise").length}{" "}
                      em análise
                    </p>
                    <span>
                      {pending.length
                        ? "Ver moderação →"
                        : "Nenhuma ocorrência pendente"}
                    </span>
                  </button>
                )}
                {data.role === "ADMIN" && (
                  <div className="adm-columns">
                    <section className="adm-card">
                      <h2>Cadastros recentes</h2>
                      <strong className="adm-number">
                        +{data.metrics.new}
                      </strong>
                      <p>Participantes na última hora</p>
                      <button
                        onClick={() => {
                          navigate("participants");
                          setRecent(true);
                        }}
                      >
                        Ver novos participantes →
                      </button>
                    </section>
                    <section className="adm-card">
                      <h2>Resumo do evento</h2>
                      <p>
                        {data.metrics.active} ativos agora ·{" "}
                        {
                          data.participants.filter(
                            (p) => p.status === "Cadastro incompleto",
                          ).length
                        }{" "}
                        cadastros incompletos
                      </p>
                      {moderate && (
                        <p>
                          {data.cases.length} ocorrências ·{" "}
                          {data.metrics.blocks} bloqueios
                        </p>
                      )}
                      <small>
                        Atividade recente: acesso à API nos últimos cinco
                        minutos. Situação administrativa e presença são
                        independentes.
                      </small>
                    </section>
                  </div>
                )}
                {!mock && <NotificationCenter visible onUnread={() => {}} />}
                {joinUrl && (
                  <button
                    className="adm-primary adm-wide"
                    onClick={() => navigate("qr")}
                  >
                    ▦ Exibir QR Code de acesso
                  </button>
                )}
                {data.event.status === "Encerrado" && (
                  <button onClick={() => navigate("report")}>
                    Ver relatório final
                  </button>
                )}
              </>
            )}
            {page === "participants" && (
              <>
                <div className="adm-heading">
                  <div>
                    <h1>Participantes</h1>
                    <p>{data.metrics.participants} cadastrados</p>
                  </div>
                  <button onClick={() => setShowFilters(!showFilters)}>
                    Filtros
                  </button>
                </div>
                <input
                  className="adm-search"
                  aria-label="Buscar por nome ou e-mail"
                  placeholder="Buscar por nome ou e-mail"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <div className="adm-tabs">
                  {["Todos", "Ativo", "Novos"].map((t) => (
                    <button
                      key={t}
                      className={
                        (t === "Novos" ? recent : !recent && status === t)
                          ? "selected"
                          : ""
                      }
                      onClick={() => {
                        setRecent(t === "Novos");
                        setStatus(t === "Novos" ? "Todos" : t);
                      }}
                    >
                      {t === "Ativo" ? "Ativos" : t}
                    </button>
                  ))}
                </div>
                {showFilters && (
                  <section className="adm-card adm-filters">
                    <label>
                      Situação
                      <select
                        aria-label="Situação"
                        value={status}
                        onChange={(e) => setStatus(e.target.value)}
                      >
                        {[
                          "Todos",
                          "Ativo",
                          "Cadastro incompleto",
                          "Suspenso",
                          "Banido",
                        ].map((s) => (
                          <option key={s}>{s}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Ordenação
                      <select
                        value={order}
                        onChange={(e) => setOrder(e.target.value)}
                      >
                        {[
                          "Nome",
                          "Cadastro mais recente",
                          "Atividade recente",
                        ].map((s) => (
                          <option key={s}>{s}</option>
                        ))}
                      </select>
                    </label>
                    {moderate && (
                      <label>
                        Moderação
                        <select
                          value={moderationFilter}
                          onChange={(e) => setModerationFilter(e.target.value)}
                        >
                          {[
                            "Todos",
                            "Sem ocorrências",
                            "Com denúncias",
                            "Com bloqueios",
                            "Sob análise",
                          ].map((s) => (
                            <option key={s}>{s}</option>
                          ))}
                        </select>
                      </label>
                    )}
                    <label>
                      <input
                        type="checkbox"
                        checked={recent}
                        onChange={(e) => setRecent(e.target.checked)}
                      />{" "}
                      Cadastro na última hora
                    </label>
                    <button
                      onClick={() => {
                        setStatus("Todos");
                        setRecent(false);
                        setModerationFilter("Todos");
                        setOrder("Nome");
                      }}
                    >
                      Limpar filtros
                    </button>
                    <button
                      className="adm-primary"
                      onClick={() => setShowFilters(false)}
                    >
                      Aplicar
                    </button>
                  </section>
                )}
                <section className="adm-card adm-list">
                  {filtered.map(personRow)}
                  {!filtered.length && <p>Nenhum participante encontrado.</p>}
                </section>
              </>
            )}
            {page === "moderation" && moderate && (
              <>
                <div className="adm-heading">
                  <div>
                    <h1>Moderação</h1>
                    <p>{pending.length} requerem atenção</p>
                  </div>
                  <button onClick={() => setShowFilters(!showFilters)}>
                    Filtros
                  </button>
                </div>
                <input
                  className="adm-search"
                  placeholder="Buscar participante ou ocorrência"
                  aria-label="Buscar participante ou ocorrência"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <div className="adm-tabs">
                  {["Todos", "Pendente", "Em análise", "Resolvida"].map((t) => (
                    <button
                      key={t}
                      className={status === t ? "selected" : ""}
                      onClick={() => setStatus(t)}
                    >
                      {t}
                    </button>
                  ))}
                </div>
                {showFilters && (
                  <section className="adm-card adm-filters">
                    <label>
                      Tipo
                      <select
                        aria-label="Tipo de ocorrência"
                        value={caseType}
                        onChange={(e) => setCaseType(e.target.value)}
                      >
                        {[
                          "Todos",
                          "Denúncia",
                          "Administrativa",
                          "Sinais de bloqueio",
                        ].map((t) => (
                          <option key={t}>{t}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Motivo
                      <input
                        aria-label="Filtrar motivo"
                        value={caseReason}
                        onChange={(e) => setCaseReason(e.target.value)}
                        placeholder="Buscar motivo registrado"
                      />
                    </label>
                    <label>
                      Período
                      <select
                        aria-label="Período das ocorrências"
                        value={casePeriod}
                        onChange={(e) => setCasePeriod(e.target.value)}
                      >
                        {["Todos", "Hoje", "Últimos 7 dias"].map((t) => (
                          <option key={t}>{t}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Ordenação
                      <select
                        aria-label="Ordenar ocorrências"
                        value={caseOrder}
                        onChange={(e) => setCaseOrder(e.target.value)}
                      >
                        {["Mais recentes", "Mais antigas", "Prioridade"].map(
                          (t) => (
                            <option key={t}>{t}</option>
                          ),
                        )}
                      </select>
                    </label>
                    <div className="adm-actions">
                      <button
                        onClick={() => {
                          setCaseType("Todos");
                          setCaseReason("");
                          setCasePeriod("Todos");
                          setCaseOrder("Mais recentes");
                          setStatus("Todos");
                        }}
                      >
                        Limpar filtros
                      </button>
                      <button
                        className="adm-primary"
                        onClick={() => setShowFilters(false)}
                      >
                        Aplicar
                      </button>
                    </div>
                  </section>
                )}
                {filteredCases
                  .sort((a, b) =>
                    caseOrder === "Prioridade"
                      ? b.priority - a.priority ||
                        new Date(b.created).getTime() -
                          new Date(a.created).getTime()
                      : caseOrder === "Mais antigas"
                        ? new Date(a.created).getTime() -
                          new Date(b.created).getTime()
                        : new Date(b.created).getTime() -
                          new Date(a.created).getTime(),
                  )
                  .map(caseRow)}
                {!filteredCases.length && (
                  <section className="adm-card">
                    Nenhuma ocorrência encontrada.
                  </section>
                )}
                {status === "Todos" &&
                  ["Todos", "Sinais de bloqueio"].includes(caseType) &&
                  !caseReason && (
                    <section className="adm-card">
                      <h2>Indicadores de bloqueios</h2>
                      <small>
                        Consulta de contexto, sem abertura automática de
                        denúncia ou limiar de alerta.
                      </small>
                      {data.blockSignals
                        .filter((s) =>
                          s.participant.name
                            .toLocaleLowerCase()
                            .includes(search.toLocaleLowerCase()),
                        )
                        .map((s) => (
                          <button
                            className="adm-person"
                            key={s.participant.id}
                            onClick={() => setSignalId(s.participant.id)}
                          >
                            <CachedImage src={s.participant.image} alt="" />
                            <span>
                              <strong>{s.participant.name}</strong>
                              <small>
                                {s.timeline.length} bloqueios recebidos
                              </small>
                            </span>
                            <span aria-hidden="true">›</span>
                          </button>
                        ))}
                      {!data.blockSignals.length && (
                        <p>Nenhum bloqueio registrado neste evento.</p>
                      )}
                    </section>
                  )}
              </>
            )}
            {page === "event" && (
              <>
                <h1>Dados do evento</h1>
                {!mock && data.role === "ADMIN" && (
                  <EventOperations
                    eventId={data.event.id}
                    onChanged={() => {
                      void adminRequest<AdminData>("event-admin/").then(
                        setData,
                      );
                    }}
                  />
                )}
                {!mock && data.role === "ADMIN" && (
                  <EventConfiguration
                    key={`${data.event.id}:${data.event.state}`}
                    eventId={data.event.id}
                    canEditDates={data.globalContext}
                  />
                )}
                <section className="adm-event-cover">
                  <h2>{data.event.name}</h2>
                  <p>{data.event.description}</p>
                </section>
                <section className="adm-card">
                  <dl>
                    <dt>Início</dt>
                    <dd>{date(data.event.starts)}</dd>
                    <dt>Término</dt>
                    <dd>{date(data.event.ends)}</dd>
                    <dt>UUID do evento</dt>
                    <dd>{data.event.id}</dd>
                    <dt>Administradores responsáveis</dt>
                    <dd>
                      {data.event.responsible.join(", ") || "Não definido"}
                    </dd>
                    <dt>Status</dt>
                    <dd>
                      <Badge>{data.event.status}</Badge>
                    </dd>
                  </dl>
                  <small>
                    Informações definidas pela administração da plataforma.
                  </small>
                </section>
                {joinUrl ? (
                  <button
                    className="adm-primary adm-wide"
                    onClick={() => navigate("qr")}
                  >
                    Exibir QR Code
                  </button>
                ) : (
                  <section className="adm-card">
                    Evento encerrado: novos ingressos estão desabilitados.
                  </section>
                )}
              </>
            )}
            {page === "qr" && (
              <>
                <h1>Acesso ao evento</h1>
                {joinUrl ? (
                  <section
                    className={`adm-card adm-qr ${fullscreen ? "adm-qr-fullscreen" : ""}`}
                  >
                    <button onClick={() => setFullscreen(!fullscreen)}>
                      {fullscreen ? "Sair da tela cheia" : "Tela cheia"}
                    </button>
                    {qr && (
                      <CachedImage
                        src={qr}
                        alt={`QR Code de ingresso no evento ${data.event.name}`}
                      />
                    )}
                    <h2>{data.event.name}</h2>
                    <p>
                      Escaneie para entrar ou criar sua conta e completar o
                      perfil neste evento.
                    </p>
                    <input
                      readOnly
                      aria-label="URL de acesso ao evento"
                      value={joinUrl}
                    />
                    <div className="adm-actions">
                      <button
                        className="adm-primary"
                        onClick={() =>
                          void run(async () => {
                            if (navigator.share)
                              await navigator.share({
                                title: data.event.name,
                                url: joinUrl,
                              });
                            else {
                              await navigator.clipboard.writeText(joinUrl);
                              setNotice("Link copiado.");
                            }
                          })
                        }
                      >
                        Compartilhar acesso
                      </button>
                      <button
                        onClick={() =>
                          void run(async () => {
                            await navigator.clipboard.writeText(joinUrl);
                            setNotice("Link copiado.");
                          })
                        }
                      >
                        Copiar link
                      </button>
                      <a download="evento-qr.png" href={qr}>
                        Baixar QR Code
                      </a>
                    </div>
                    <ol>
                      <li>Escaneie com a câmera do celular.</li>
                      <li>Entre ou crie uma conta.</li>
                      <li>Complete seu perfil para participar.</li>
                    </ol>
                    <small>
                      {mock
                        ? "QR Code demonstrativo: abre a prévia do participante neste evento, sem cadastro no banco."
                        : "O link expira em 30 dias e deixa de aceitar ingressos ao encerrar o evento."}
                    </small>
                  </section>
                ) : (
                  <p>Novos ingressos indisponíveis: evento encerrado.</p>
                )}
              </>
            )}
            {page === "more" && (
              <>
                <h1>Mais</h1>
                <section
                  className="adm-card adm-actions"
                  aria-label="Conta e opções do evento"
                >
                  {data.role === "ADMIN" && (
                    <button onClick={() => navigate("team")}>
                      Equipe do evento ›
                    </button>
                  )}
                  {data.role === "ADMIN" && (
                    <button onClick={() => navigate("report")}>
                      Relatório do evento ›
                    </button>
                  )}
                  <button
                    className="account-logout"
                    disabled={busy}
                    onClick={() => void run(onLogout)}
                  >
                    Sair da conta
                  </button>
                </section>
                {!mock && data.permissions?.includes("announcements") && (
                  <Announcements readOnly={readOnly} />
                )}
                {!mock && moderate && <SupportPanel admin />}
                {!mock && data.permissions?.includes("passes") && (
                  <PassManagement role={data.role} readOnly={readOnly} />
                )}
              </>
            )}
            {page === "team" && data.role === "ADMIN" && (
              <>
                <h1>Equipe do evento</h1>
                <p>Papéis e vínculos administrativos</p>
                {!mock && (
                  <TeamManagement
                    eventId={data.event.id}
                    readOnly={readOnly}
                    onChanged={() => void fetchData()}
                  />
                )}
                <section className="adm-card">
                  {data.team.map((m) => (
                    <article key={m.id}>
                      <strong>{m.name}</strong>
                      <p>
                        <Badge>{m.role}</Badge>
                      </p>
                    </article>
                  ))}
                  {mock && (
                    <small>
                      Alterações de equipe são realizadas no Django Admin pela
                      equipe autorizada.
                    </small>
                  )}
                </section>
              </>
            )}
            {page === "report" && data.role === "ADMIN" && (
              <>
                <h1>Relatório do evento</h1>
                {!mock && <FinancialReport />}
                <p>
                  {data.event.status === "Encerrado"
                    ? "Consolidação final"
                    : "Resultados parciais"}{" "}
                  · {data.event.name}
                </p>
                {stats}
                {moderate && (
                  <section className="adm-card">
                    <h2>Segurança</h2>
                    <p>
                      {data.cases.length} ocorrências · {data.metrics.blocks}{" "}
                      bloqueios
                    </p>
                    <p>
                      {pending.length} em aberto ·{" "}
                      {data.cases.length - pending.length} resolvidas
                    </p>
                  </section>
                )}
                <small>
                  Indicadores agregados do banco de dados, sem acesso às
                  conversas privadas.
                </small>
              </>
            )}
          </>
        )}
      </main>
      <AdminNavigation
        current={
          page === "qr"
            ? "event"
            : ["team", "report"].includes(page)
              ? "more"
              : page
        }
        disabled={busy}
        items={[
          ...pages
            .filter(([p]) => p !== "moderation" || moderate)
            .map(([p, label]) => ({
              key: p,
              label,
              icon: (
                {
                  dashboard: "home",
                  participants: "people",
                  moderation: "shield",
                  event: "calendar",
                  more: "more",
                } as Record<string, AdminNavItem["icon"]>
              )[p],
              badge: p === "moderation" ? pending.length : undefined,
            })),
          ...(!mock && data.globalContext && onContext
            ? [{ key: "global", label: "Global", icon: "global" as const }]
            : []),
        ]}
        onSelect={(key) =>
          key === "global" ? onContext?.(true) : navigate(key as Page)
        }
      />
      <dialog
        ref={dialog}
        className="adm-dialog"
        onCancel={() => setAction(null)}
        onClick={(e) => closeDialogOnBackdrop(e, () => setAction(null))}
      >
        <form onSubmit={execute}>
          <button
            type="button"
            className="adm-dialog-close"
            aria-label="Fechar"
            onClick={() => setAction(null)}
          >
            ×
          </button>
          <h2>
            {action === "assume"
              ? "Assumir caso"
              : action === "ban"
                ? "Banir participante do evento"
                : action === "suspend"
                  ? "Suspender participante"
                  : action === "reactivate"
                    ? "Reativar participante"
                    : action === "note"
                      ? "Adicionar nota interna"
                      : action === "reopen"
                        ? "Reabrir ocorrência"
                        : action === "report"
                          ? "Abrir ocorrência administrativa"
                          : "Resolver ocorrência"}
          </h2>
          <p>{occurrence?.reported.name || person?.name}</p>
          {action === "assume" && (
            <p>
              Confirmar que deseja assumir a responsabilidade por este caso?
            </p>
          )}
          {action === "resolve" && (
            <label>
              <input
                type="checkbox"
                checked={unfounded}
                onChange={(e) => setUnfounded(e.target.checked)}
              />
              Denúncia considerada infundada; não entra nos limites de dez e
              vinte denúncias.
            </label>
          )}
          {action === "ban" && (
            <p>O acesso a este evento será removido definitivamente.</p>
          )}
          {action === "suspend" && (
            <p>
              O acesso a este evento ficará restrito até reativação
              administrativa.
            </p>
          )}
          {action === "resolve" && (
            <label>
              Conclusão
              <select
                required
                value={selectedReason}
                onChange={(e) => setSelectedReason(e.target.value)}
              >
                <option value="">Selecionar conclusão</option>
                {[
                  "Elementos insuficientes",
                  "Situação resolvida",
                  "Denúncia duplicada",
                  "Decisão administrativa concluída",
                  "Outro",
                ].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
          )}
          {action === "report" && (
            <label>
              Motivo
              <input
                required
                maxLength={200}
                value={selectedReason}
                onChange={(e) => setSelectedReason(e.target.value)}
                placeholder="Motivo da ocorrência"
              />
            </label>
          )}
          <label>
            {action === "note" ? "Nota interna" : "Motivo e justificativa"}
            <textarea
              required={action !== "assume"}
              maxLength={3500}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Descreva o contexto e a decisão…"
            />
          </label>
          {action === "ban" && (
            <label className="adm-checkbox">
              <input
                type="checkbox"
                required
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
              />{" "}
              Estou ciente de que esta ação remove o acesso somente a este
              evento.
            </label>
          )}
          {error && (
            <p role="alert" className="adm-form-error">
              {error}
            </p>
          )}
          <small>A ação será registrada no histórico de auditoria.</small>
          <div className="adm-actions">
            <button type="button" onClick={() => setAction(null)}>
              Cancelar
            </button>
            <button
              disabled={busy}
              className={action === "ban" ? "adm-danger-button" : "adm-primary"}
              type="submit"
            >
              {busy ? "Salvando…" : "Confirmar"}
            </button>
          </div>
        </form>
      </dialog>
    </div>
  );
}
