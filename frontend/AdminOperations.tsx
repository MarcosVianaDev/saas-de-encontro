import { CachedImage } from "./CachedImage";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { request } from "./backend-client";
import { SupportPanel } from "./ParticipantExtras";
import { FormattedText } from "./FormattedText";

type Intervention = {
  bio: string;
  photos: { id: string; url: string }[];
  sources: { id: string; kind: string; label: string }[];
};
export function ProfileIntervention({
  id,
  onChanged,
  permissions,
}: {
  id: string;
  onChanged: () => void;
  permissions: string[];
}) {
  const [data, setData] = useState<Intervention | null>(null),
    [source, setSource] = useState(""),
    [photo, setPhoto] = useState(""),
    [bio, setBio] = useState(""),
    [reason, setReason] = useState(""),
    [action, setAction] = useState("remove_photo"),
    [confirm, setConfirm] = useState(false),
    [status, setStatus] = useState("");
  const load = () =>
    request<Intervention>(
      `event-admin/participants/${id}/profile-intervention/`,
    )
      .then((d) => {
        setData(d);
        setBio(d.bio);
      })
      .catch((e) => setStatus(e.message));
  useEffect(() => {
    void load();
  }, [id]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!confirm) {
      setConfirm(true);
      return;
    }
    const s = data?.sources.find((s) => `${s.kind}:${s.id}` === source);
    try {
      await request(
        `event-admin/participants/${id}/profile-intervention/`,
        "POST",
        { action, photo, bio, reason, source: s?.id, kind: s?.kind },
      );
      setConfirm(false);
      setStatus("Intervenção registrada e participante notificado.");
      void load();
      onChanged();
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Não foi possível concluir.");
    }
  }
  return (
    <section className="adm-card">
      <h2>Intervenção no perfil</h2>
      <p>
        As fotos públicas aprovadas não podem ser trocadas pelo participante. A
        intervenção exige uma ocorrência ou atendimento e fica auditada.
      </p>
      <form onSubmit={submit}>
        <label>
          Origem
          <select
            required
            value={source}
            onChange={(e) => {
              setSource(e.target.value);
              setConfirm(false);
            }}
          >
            <option value="">Selecione denúncia ou atendimento</option>
            {data?.sources.map((s) => (
              <option key={`${s.kind}:${s.id}`} value={`${s.kind}:${s.id}`}>
                {s.kind === "report" ? "Denúncia" : "Atendimento"}: {s.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Ação
          <select
            value={action}
            onChange={(e) => {
              setAction(e.target.value);
              setConfirm(false);
            }}
          >
            {permissions.includes("remove_photo") && (
              <option value="remove_photo">Remover foto pública</option>
            )}
            {permissions.includes("edit_bio") && (
              <option value="edit_bio">Editar descrição</option>
            )}
          </select>
        </label>
        {action === "remove_photo" ? (
          <>
            <label>
              Foto
              <select
                required
                value={photo}
                onChange={(e) => {
                  setPhoto(e.target.value);
                  setConfirm(false);
                }}
              >
                <option value="">Selecione a foto</option>
                {data?.photos.map((p, i) => (
                  <option key={p.id} value={p.id}>
                    Foto pública {i + 1}
                  </option>
                ))}
              </select>
            </label>
            {photo && (
              <CachedImage
                width={140}
                src={data?.photos.find((p) => p.id === photo)?.url}
                alt="Foto selecionada"
              />
            )}
          </>
        ) : (
          <label>
            Descrição
            <textarea
              minLength={50}
              maxLength={4000}
              required
              value={bio}
              onChange={(e) => {
                setBio(e.target.value);
                setConfirm(false);
              }}
            />
          </label>
        )}
        <label>
          Motivo
          <textarea
            required
            maxLength={4000}
            value={reason}
            onChange={(e) => {
              setReason(e.target.value);
              setConfirm(false);
            }}
          />
        </label>
        {confirm && (
          <p role="alert">
            Confirmar esta intervenção? A remoção de foto desativa o perfil para
            revisão e preserva a imagem no histórico restrito.
          </p>
        )}
        <button type="button" onClick={() => setConfirm(false)}>
          Cancelar
        </button>
        <button>
          {confirm ? "Confirmar intervenção" : "Revisar intervenção"}
        </button>
      </form>
      {status && <p role="status">{status}</p>}
    </section>
  );
}

type PassData = {
  canEditOffers: boolean;
  offers: {
    id: string;
    name: string;
    price: string;
    limit: number | null;
    durationMinutes: number | null;
  }[];
  passes: {
    id: string;
    participant: string;
    name: string;
    amount: string;
    created: string;
    revoked: string | null;
    origin: string;
  }[];
};
export function PassManagement({
  participantId,
  role,
  readOnly = false,
}: {
  participantId?: string;
  role: string;
  readOnly?: boolean;
}) {
  const [data, setData] = useState<PassData | null>(null),
    [offer, setOffer] = useState(""),
    [origin, setOrigin] = useState(""),
    [reference, setReference] = useState(""),
    [reason, setReason] = useState(""),
    [revoke, setRevoke] = useState(""),
    [error, setError] = useState(""),
    [name, setName] = useState(""),
    [price, setPrice] = useState("0"),
    [limit, setLimit] = useState("10"),
    [minutes, setMinutes] = useState("0"),
    [granting, setGranting] = useState(false);
  const [editingOffer, setEditingOffer] = useState("");
  const load = () =>
    request<PassData>("event-admin/passes/")
      .then((d) => {
        setData(d);
        setOffer(d.offers[0]?.id || "");
      })
      .catch((e) => setError(e.message));
  useEffect(() => {
    void load();
  }, [participantId]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    try {
      await request("event-admin/passes/", "POST", {
        participant: participantId,
        offer,
        origin,
        reference,
      });
      setError("Passe ativado para o participante.");
      setGranting(false);
      void load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível conceder.");
    }
  }
  return (
    <section className="adm-card">
      {!readOnly && role === "OPERATOR" && participantId && !granting && (
        <button onClick={() => setGranting(true)}>Conceder passe</button>
      )}
      {!readOnly && role === "OPERATOR" && participantId && granting && (
        <form onSubmit={submit}>
          <label>
            Oferta
            <select
              required
              value={offer}
              onChange={(e) => setOffer(e.target.value)}
            >
              {data?.offers.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name} · R$ {o.price}
                </option>
              ))}
            </select>
          </label>
          <label>
            Origem
            <input
              required
              maxLength={100}
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
            />
          </label>
          <label>
            Observação ou referência
            <input
              value={reference}
              maxLength={500}
              onChange={(e) => setReference(e.target.value)}
            />
          </label>
          <button type="button" onClick={() => setGranting(false)}>
            Cancelar
          </button>
          <button className="adm-primary">Confirmar concessão</button>
        </form>
      )}
      {!participantId &&
        data?.offers.map((o) => (
          <article key={o.id}>
            <h3>{o.name}</h3>
            <p>
              {o.limit
                ? `${o.limit} revelações`
                : `${o.durationMinutes} minutos`}{" "}
              · R$ {o.price}
            </p>
            {data.canEditOffers && !readOnly && (
              <button
                onClick={() => {
                  setEditingOffer(o.id);
                  setName(o.name);
                  setPrice(o.price);
                  setLimit(String(o.limit || 0));
                  setMinutes(String(o.durationMinutes || 0));
                }}
              >
                Editar oferta
              </button>
            )}
          </article>
        ))}
      {!readOnly &&
        data?.canEditOffers &&
        role === "ADMIN" &&
        !participantId && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void request("event-admin/passes/", "POST", {
                action: "offer",
                id: editingOffer || undefined,
                name,
                price,
                limit,
                minutes,
              })
                .then(() => {
                  void load();
                  setError(
                    editingOffer
                      ? "Oferta atualizada. Concessões anteriores preservadas."
                      : "Oferta criada.",
                  );
                })
                .catch((e) => setError(e.message));
            }}
          >
            <h3>{editingOffer ? "Editar oferta" : "Nova oferta"}</h3>
            {editingOffer && (
              <button
                type="button"
                onClick={() => {
                  setEditingOffer("");
                  setName("");
                  setPrice("0");
                  setLimit("10");
                  setMinutes("0");
                }}
              >
                Criar outra oferta
              </button>
            )}
            <label>
              Nome
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </label>
            <label>
              Valor configurado (R$)
              <input
                type="number"
                min="0"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
              />
            </label>
            <label>
              Quantidade de revelações (0 para passe por tempo)
              <input
                type="number"
                min="0"
                value={limit}
                onChange={(e) => setLimit(e.target.value)}
              />
            </label>
            <label>
              Duração em minutos (0 para passe por quantidade)
              <input
                type="number"
                min="0"
                value={minutes}
                onChange={(e) => setMinutes(e.target.value)}
              />
            </label>
            <button>Salvar oferta</button>
          </form>
        )}
      {data?.passes
        .filter((p) => !participantId || p.participant === participantId)
        .map((p) => (
          <article key={p.id}>
            <strong>{p.name}</strong>
            <p>
              R$ {p.amount} · {p.origin} ·{" "}
              {new Date(p.created).toLocaleString("pt-BR")}
            </p>
            {p.revoked ? (
              <p>Passe revogado; lançamento original preservado.</p>
            ) : (
              !readOnly && (
                <button onClick={() => setRevoke(p.id)}>Revogar passe</button>
              )
            )}
          </article>
        ))}
      {revoke && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void request("event-admin/passes/", "POST", {
              action: "revoke",
              id: revoke,
              reason,
            })
              .then(() => {
                setRevoke("");
                void load();
              })
              .catch((e) => setError(e.message));
          }}
        >
          <p>A revogação não remove a venda declarada.</p>
          <label>
            Motivo
            <textarea
              required
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </label>
          <button type="button" onClick={() => setRevoke("")}>
            Cancelar
          </button>
          <button>Confirmar revogação</button>
        </form>
      )}
      {error && <p role="status">{error}</p>}
    </section>
  );
}

export function FinancialReport() {
  const [data, setData] = useState<{
      total: string;
      notice: string;
      sales: {
        id: string;
        type: string;
        amount: string;
        free: boolean;
        operator: string;
        created: string;
        revoked: string | null;
      }[];
    } | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    void request<typeof data>("event-admin/financial/")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section className="adm-card">
      <h2>Relatório financeiro</h2>
      <p>{data?.notice}</p>
      <strong>Total declarado: R$ {data?.total || "0"}</strong>
      {data?.sales.map((p) => (
        <article key={p.id}>
          <p>
            {p.type} · {p.free ? "Cortesia" : `R$ ${p.amount}`} · {p.operator} ·{" "}
            {new Date(p.created).toLocaleString("pt-BR")}
            {p.revoked ? " · Revogado" : ""}
          </p>
        </article>
      ))}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}

export function ParticipantOperation({
  id,
  onChanged,
  manager = false,
  permissions,
  historyAllowed = false,
  canInvestigate = false,
  gpsEnabled = true,
}: {
  id: string;
  onChanged: () => void;
  manager?: boolean;
  permissions: string[];
  historyAllowed?: boolean;
  canInvestigate?: boolean;
  gpsEnabled?: boolean;
}) {
  const fileRef = useRef<HTMLInputElement>(null),
    [exceptionModal, setExceptionModal] = useState(false),
    [investigation, setInvestigation] = useState(""),
    [resolution, setResolution] = useState("DISCARDED"),
    [file, setFile] = useState<File | null>(null),
    [preview, setPreview] = useState(""),
    [error, setError] = useState(""),
    [reason, setReason] = useState(""),
    [minutes, setMinutes] = useState("15"),
    [history, setHistory] = useState<
      | {
          latitude: number;
          longitude: number;
          distance: number;
          speed: number | null;
          accuracy: number;
          measured: string;
          anomalous: boolean;
          anomaly: {
            id: string;
            criterion: string;
            resolution: string;
            reason: string;
          } | null;
        }[]
      | null
    >(null);
  useEffect(() => {
    if (!file) {
      setPreview("");
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  const perform = (path: string, body: unknown) =>
    request(`event-admin/participants/${id}/${path}/`, "POST", body)
      .then(() => {
        setError("Operação registrada.");
        onChanged();
        return true;
      })
      .catch((e) => {
        setError(e.message);
        return false;
      });
  return (
    <section className="adm-card">
      <h2>Ativação e presença</h2>
      {permissions.includes("outfit") && (
        <>
          <input
            hidden
            ref={fileRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <button onClick={() => fileRef.current?.click()}>
            Capturar foto
          </button>
          {preview && (
            <>
              <CachedImage
                src={preview}
                alt="Prévia da foto do look"
                style={{ maxWidth: 240 }}
              />
              <button
                onClick={() => {
                  const form = new FormData();
                  form.append("file", file!);
                  void perform("outfit", form).then((ok) => {
                    if (ok) setFile(null);
                  });
                }}
              >
                Usar esta foto
              </button>
              <button onClick={() => fileRef.current?.click()}>
                Tirar novamente
              </button>
            </>
          )}
        </>
      )}
      {permissions.includes("activation") && (
        <button
          className="adm-primary"
          onClick={() => void perform("activate", {})}
        >
          Ativar perfil
        </button>
      )}
      {gpsEnabled && (permissions.includes("location_exception") || manager) && (
        <label>
          Motivo da intervenção ou consulta
          <textarea
            value={reason}
            maxLength={4000}
            onChange={(e) => setReason(e.target.value)}
          />
        </label>
      )}
      {gpsEnabled && permissions.includes("location_exception") && (
        <button onClick={() => setExceptionModal(true)}>
          Ignorar verificação temporariamente
        </button>
      )}
      {gpsEnabled && exceptionModal && (
        <section
          role="dialog"
          aria-modal="true"
          aria-label="Exceção de localização"
        >
          <label>
            Duração da exceção (minutos)
            <input
              type="number"
              min="1"
              value={minutes}
              onChange={(e) => setMinutes(e.target.value)}
            />
          </label>
          <p>
            O participante permanecerá ativo durante o período definido mesmo
            sem uma nova validação de localização.
          </p>
          <button
            onClick={() =>
              void perform("location-exception", {
                minutes: Number(minutes),
                reason,
              }).then((ok) => {
                if (ok) setExceptionModal(false);
              })
            }
          >
            Reativar temporariamente
          </button>
          <button onClick={() => setExceptionModal(false)}>Cancelar</button>
        </section>
      )}
      {gpsEnabled && manager && (
        <button
          disabled={!historyAllowed}
          onClick={() =>
            void request<NonNullable<typeof history>>(
              `event-admin/participants/${id}/location-history/`,
              "POST",
              { reason },
            )
              .then(setHistory)
              .catch((e) => setError(e.message))
          }
        >
          Consultar histórico de localização
        </button>
      )}
      {history && (
        <section>
          <h3>Histórico individual restrito</h3>
          {history.map((r, i) => (
            <p key={i}>
              {new Date(r.measured).toLocaleString("pt-BR")} ·{" "}
              {r.latitude.toFixed(5)}, {r.longitude.toFixed(5)} · Distância:{" "}
              {Math.round(r.distance)} m · Precisão: {Math.round(r.accuracy)} m
              · Velocidade:{" "}
              {r.speed == null ? "Não calculada" : `${r.speed.toFixed(1)} km/h`}
              {r.anomalous ? " · Sinal de anomalia" : ""}
              {r.anomaly && (
                <>
                  <br />
                  {r.anomaly.criterion === "DISTANCE"
                    ? "Duas leituras além do limite"
                    : "Sinal de velocidade"}{" "}
                  · {r.anomaly.resolution || "Sem decisão"}
                  {r.anomaly.reason && ` · ${r.anomaly.reason}`}
                  {canInvestigate && (
                    <button
                      onClick={() => {
                        setInvestigation(r.anomaly!.id);
                        setResolution("DISCARDED");
                      }}
                    >
                      Registrar desfecho
                    </button>
                  )}
                </>
              )}
            </p>
          ))}
        </section>
      )}
      {manager && !historyAllowed && (
        <p>
          O histórico só pode ser consultado com o evento pausado, encerrado ou
          arquivado. Pause o evento para investigar.
        </p>
      )}
      {investigation && (
        <section
          role="dialog"
          aria-modal="true"
          aria-label="Decisão sobre localização"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void perform("location-decision", {
                anomaly: investigation,
                resolution,
                reason,
                confirmed: true,
              }).then((ok) => {
                if (ok) {
                  setInvestigation("");
                  setHistory(null);
                }
              });
            }}
          >
            <h3>Confirmar decisão sobre a anomalia?</h3>
            <p>
              O sinal não constitui punição automática. Uma decisão de banimento
              vale somente neste evento e pode ser revertida pela gestão
              autorizada.
            </p>
            <label>
              Desfecho
              <select
                value={resolution}
                onChange={(e) => setResolution(e.target.value)}
              >
                <option value="DISCARDED">Anomalia descartada</option>
                <option value="NO_RESTRICTION">Tratado sem restrição</option>
                <option value="EVENT_BAN">Banimento do evento</option>
                <option value="REVOKE_BAN">
                  Revogar banimento decorrente desta anomalia
                </option>
              </select>
            </label>
            <label>
              Justificativa
              <textarea
                required
                maxLength={4000}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </label>
            <button type="button" onClick={() => setInvestigation("")}>
              Cancelar
            </button>
            <button>Confirmar decisão</button>
          </form>
        </section>
      )}
      {error && <p role="status">{error}</p>}
    </section>
  );
}

type Announcement = {
  id: string;
  title: string;
  body: string;
  url: string;
  state: string;
  scheduled: string | null;
  sent: string | null;
};
export function Announcements({
  readOnly = false,
  eventState,
  starts,
  ends,
}: {
  readOnly?: boolean;
  eventState?: string;
  starts?: string | null;
  ends?: string | null;
}) {
  const canSend = ["OPEN", "RUNNING", "PAUSED"].includes(eventState || "");
  const localDateTime = (value: string | null | undefined) =>
    value
      ? new Date(
          new Date(value).getTime() - new Date(value).getTimezoneOffset() * 60000,
        )
          .toISOString()
          .slice(0, 16)
      : undefined;
  const [items, setItems] = useState<Announcement[]>([]),
    [tab, setTab] = useState("Todos"),
    [editor, setEditor] = useState(false),
    [draft, setDraft] = useState({
      id: "",
      title: "",
      body: "",
      url: "",
      scheduled: "",
    }),
    [action, setAction] = useState("draft"),
    [confirmation, setConfirmation] = useState(false),
    [error, setError] = useState("");
  const load = () =>
    request<Announcement[]>("event-admin/announcements/")
      .then(setItems)
      .catch((e) => setError(e.message));
  useEffect(() => {
    void load();
  }, []);
  const execute = async (e: FormEvent) => {
    e.preventDefault();
    if (action === "schedule") {
      const scheduled = new Date(draft.scheduled).getTime();
      if (
        !starts ||
        !ends ||
        !Number.isFinite(scheduled) ||
        scheduled <= Date.now() ||
        scheduled < new Date(starts).getTime() ||
        scheduled >= new Date(ends).getTime()
      ) {
        setError(
          "Agende um horário futuro a partir do início e antes do término previsto do evento.",
        );
        return;
      }
    }
    if (action !== "draft" && !confirmation) {
      setConfirmation(true);
      return;
    }
    try {
      await request("event-admin/announcements/", "POST", {
        ...draft,
        id: draft.id || undefined,
        action,
        scheduled: draft.scheduled
          ? new Date(draft.scheduled).toISOString()
          : undefined,
        confirmed: confirmation,
      });
      setEditor(false);
      setConfirmation(false);
      setError(action === "send" ? "Aviso enviado." : "Aviso salvo.");
      void load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível salvar.");
    }
  };
  return (
    <section className="adm-card adm-announcements">
      <div className="adm-actions adm-announcement-actions">
        {!readOnly && (
          <button
            className="adm-primary adm-new-announcement"
            onClick={() => {
              setEditor(true);
              setDraft({ id: "", title: "", body: "", url: "", scheduled: "" });
              setConfirmation(false);
              setAction("draft");
            }}
          >
            + Novo aviso
          </button>
        )}
        {["Todos", "Rascunhos", "Agendados", "Enviados"].map((t) => (
          <button key={t} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>
      {items
        .filter(
          (a) =>
            tab === "Todos" ||
            a.state ===
              (
                {
                  Rascunhos: "DRAFT",
                  Agendados: "SCHEDULED",
                  Enviados: "SENT",
                } as Record<string, string>
              )[tab],
        )
        .map((a) => (
          <article key={a.id}>
            <h3>{a.title}</h3>
            <p>
              <FormattedText text={a.body} />
            </p>
            <small>
              {(
                {
                  DRAFT: "Rascunho",
                  SCHEDULED: "Agendado",
                  SENT: "Enviado",
                  HELD: "Pausado",
                  CANCELLED: "Não enviado",
                } as Record<string, string>
              )[a.state] || a.state}{" "}
              {a.scheduled ? new Date(a.scheduled).toLocaleString("pt-BR") : ""}
            </small>
            {a.url && (
              <a href={a.url} target="_blank" rel="noopener noreferrer">
                Abrir link
              </a>
            )}
            {!readOnly && !["SENT", "CANCELLED"].includes(a.state) && (
              <button
                onClick={() => {
                  setEditor(true);
                  setDraft({
                    ...a,
                    scheduled: a.scheduled
                      ? new Date(
                          new Date(a.scheduled).getTime() -
                            new Date().getTimezoneOffset() * 60000,
                        )
                          .toISOString()
                          .slice(0, 16)
                      : "",
                  });
                  setConfirmation(false);
                  setAction(a.state === "HELD" && canSend ? "send" : "draft");
                }}
              >
                {a.state === "HELD" && canSend ? "Enviar manualmente" : "Editar"}
              </button>
            )}
          </article>
        ))}
      {!readOnly && editor && (
        <form onSubmit={execute}>
          <label>
            Título
            <input
              required
              maxLength={200}
              value={draft.title}
              onChange={(e) => setDraft({ ...draft, title: e.target.value })}
            />
          </label>
          <label>
            Mensagem (use **texto** para destaque)
            <textarea
              required
              maxLength={10000}
              value={draft.body}
              onChange={(e) => setDraft({ ...draft, body: e.target.value })}
            />
          </label>
          <label>
            Link opcional
            <input
              type="url"
              value={draft.url}
              onChange={(e) => setDraft({ ...draft, url: e.target.value })}
            />
          </label>
          <label>
            Envio
            <select
              value={action}
              onChange={(e) => {
                setAction(e.target.value);
                setConfirmation(false);
              }}
            >
              <option value="draft">Salvar rascunho</option>
              {canSend && <option value="send">Enviar agora</option>}
              <option value="schedule" disabled={!starts || !ends}>
                Agendar
              </option>
            </select>
          </label>
          {action === "schedule" && (
            <label>
              Data e horário
              <input
                required
                type="datetime-local"
                min={localDateTime(starts)}
                max={localDateTime(ends)}
                value={draft.scheduled}
                onChange={(e) =>
                  setDraft({ ...draft, scheduled: e.target.value })
                }
              />
            </label>
          )}
          <p>
            {starts && ends
              ? `Os avisos podem ser agendados a partir de ${new Date(starts).toLocaleString("pt-BR")} e antes de ${new Date(ends).toLocaleString("pt-BR")}. Se o período do evento mudar, avisos fora dele voltarão a rascunho.`
              : "Defina o início e o término do evento para agendar avisos. Você pode salvar rascunhos."}
          </p>
          {confirmation && (
            <section>
              <h3>
                {action === "send"
                  ? "Enviar este aviso para os participantes do evento?"
                  : "Confirmar agendamento?"}
              </h3>
              <h4>{draft.title}</h4>
              <p>
                <FormattedText text={draft.body} />
              </p>
              {action === "schedule" && (
                <p>
                  Se agendado nos 30 minutos finais, o aviso poderá não ser
                  enviado caso o evento seja encerrado ou esteja em estado que
                  impeça o disparo.
                </p>
              )}
            </section>
          )}
          <button
            type="button"
            onClick={() =>
              confirmation ? setConfirmation(false) : setEditor(false)
            }
          >
            {confirmation ? "Voltar" : "Cancelar"}
          </button>
          <button className="adm-primary">
            {confirmation
              ? action === "send"
                ? "Enviar aviso"
                : "Agendar mesmo assim"
              : action === "draft"
                ? "Salvar rascunho"
                : "Continuar"}
          </button>
        </form>
      )}
      {error && <p role="status">{error}</p>}
    </section>
  );
}
