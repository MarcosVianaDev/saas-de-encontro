import { useEffect, useState, type FormEvent } from "react";
import { request } from "./backend-client";

type EventInfo = {
  state: string;
  status: string;
  actions: string[];
  pendingApproval?: boolean;
  challenge?: string;
  timeline: { state: string; label: string; enteredAt?: string | null }[];
  configuration: Record<string, unknown>;
};
const labels: Record<string, string> = {
  SCHEDULED: "Agendar evento",
  OPEN: "Abrir evento",
  RUNNING: "Iniciar evento",
  PAUSED: "Pausar evento",
  CLOSED: "Encerrar evento",
};

export function EventOperations({
  eventId,
  onChanged,
}: {
  eventId: string;
  onChanged: () => void;
}) {
  const [data, setData] = useState<EventInfo | null>(null);
  const [action, setAction] = useState("");
  const [reason, setReason] = useState("");
  const [captcha, setCaptcha] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    void request<EventInfo>("event-admin/transition/")
      .then(setData)
      .catch((e) => setError(e.message));
  }, [eventId]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await request<EventInfo>(
        "event-admin/transition/",
        "POST",
        { state: action, reason, captcha, confirmed: true },
      );
      setData(result);
      setAction("");
      setCaptcha("");
      setReason("");
      onChanged();
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Não foi possível alterar o evento.",
      );
      void request<EventInfo>("event-admin/transition/").then(setData);
    } finally {
      setBusy(false);
    }
  }
  if (!data)
    return error ? (
      <p role="alert">{error}</p>
    ) : (
      <p>Carregando ciclo do evento…</p>
    );
  const actionLabel = (state: string) =>
    state === "SCHEDULED" && data.pendingApproval
      ? "Aprovar e agendar evento"
      : labels[state];
  return (
    <section className="adm-card">
      <h2>Status: {data.status}</h2>
      {data.pendingApproval && (
        <p>
          Solicitação salva como rascunho. O evento aguarda aprovação da
          Administração Global.
        </p>
      )}
      <ol className="event-timeline">
        {data.timeline.filter((item) => !["DRAFT", "ARCHIVED"].includes(item.state)).map((item) => (
          <li
            key={item.state}
            aria-current={data.state === item.state ? "step" : undefined}
          >
            <span>{item.label}</span>
            {item.enteredAt ? (
              <time
                dateTime={item.enteredAt}
                title={new Date(item.enteredAt).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}
              >
                {new Date(item.enteredAt).toLocaleTimeString("pt-BR", {
                  timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit",
                })}
              </time>
            ) : <span aria-label="Horário não registrado">—</span>}
          </li>
        ))}
      </ol>
      <div className="adm-actions">
        {data.actions.map((state) => (
          <button
            key={state}
            onClick={() => {
              setAction(state);
              void request<EventInfo>("event-admin/transition/").then(setData);
            }}
          >
            {state === "RUNNING" && data.state === "PAUSED"
              ? "Retomar evento"
              : actionLabel(state)}
          </button>
        ))}
      </div>
      {action && (
        <form onSubmit={submit}>
          <h3>
            {action === "CLOSED"
              ? "Encerrar evento antes do horário?"
              : `${actionLabel(action)}?`}
          </h3>
          {action === "PAUSED" && (
            <p>
              Novas descobertas e interações serão temporariamente
              interrompidas. Matches e conversas existentes continuarão
              disponíveis. O horário de encerramento do evento não será
              alterado.
            </p>
          )}
          {action === "CLOSED" && (
            <>
              <p>
                Esta ação encerra novas descobertas, likes, matches e mensagens.
                Os participantes serão notificados. O evento não poderá voltar
                para “Em andamento”.
              </p>
              <label>
                Motivo do encerramento
                <textarea
                  required
                  value={reason}
                  maxLength={4000}
                  onChange={(e) => setReason(e.target.value)}
                />
              </label>
              <label>
                {data.challenge}
                <input
                  required
                  value={captcha}
                  inputMode="numeric"
                  onChange={(e) => setCaptcha(e.target.value)}
                />
              </label>
            </>
          )}
          <div className="adm-actions">
            <button type="button" onClick={() => setAction("")}>
              Cancelar
            </button>
            <button disabled={busy} className="adm-primary" type="submit">
              {actionLabel(action)}
            </button>
          </div>
        </form>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
