import { useEffect, useRef, useState, type FormEvent } from "react";
import { request } from "./backend-client";
import type { Person } from "./types";
import { FormattedText } from "./FormattedText";

type Notice = {
  id: string;
  title: string;
  body: string;
  read: boolean;
  created: string;
  action: string;
};
export function NotificationCenter({
  visible,
  onUnread,
}: {
  visible: boolean;
  onUnread: (count: number) => void;
}) {
  const [items, setItems] = useState<Notice[]>([]),
    [error, setError] = useState("");
  const load = () =>
    request<{ unread: number; items: Notice[] }>("notifications/")
      .then((d) => {
        setItems(d.items);
        onUnread(d.unread);
      })
      .catch((e) => setError(e.message));
  useEffect(() => {
    void load();
    const t = setInterval(() => {
      if (!document.hidden) void load();
    }, 5000);
    return () => clearInterval(t);
  }, []);
  if (!visible) return null;
  return (
    <section className="participant-tools">
      <h2>Notificações</h2>
      {error && <p role="alert">{error}</p>}
      {!items.length && <p>Nenhuma notificação.</p>}
      {items.map((n) => (
        <article key={n.id} className={n.read ? "" : "unread"}>
          <h3>{n.title}</h3>
          <p>
            <FormattedText text={n.body} />
          </p>
          <small>{new Date(n.created).toLocaleString("pt-BR")}</small>
          {n.action &&
            (n.action.startsWith("#") ? (
              <a href={n.action}>Abrir</a>
            ) : /^https?:\/\//.test(n.action) ? (
              <a href={n.action} target="_blank" rel="noopener noreferrer">
                Abrir link
              </a>
            ) : null)}
          {!n.read && (
            <button
              onClick={() =>
                void request("notifications/", "POST", { id: n.id }).then(load)
              }
            >
              Marcar como lida
            </button>
          )}
        </article>
      ))}
    </section>
  );
}

type Thread = {
  id: string;
  subject: string;
  participant: string;
  messages: { id: string; body: string; author: string; created: string }[];
};
export function SupportPanel({ admin = false }: { admin?: boolean }) {
  const [threads, setThreads] = useState<Thread[]>([]),
    [thread, setThread] = useState(""),
    [body, setBody] = useState(""),
    [error, setError] = useState("");
  const endpoint = admin ? "event-admin/support/" : "support/";
  const load = () =>
    request<Thread[]>(endpoint)
      .then(setThreads)
      .catch((e) => setError(e.message));
  useEffect(() => {
    void load();
    const t = setInterval(() => {
      if (!document.hidden) void load();
    }, 5000);
    return () => clearInterval(t);
  }, [admin]);
  async function send(e: FormEvent) {
    e.preventDefault();
    try {
      const d = await request<Thread>(endpoint, "POST", {
        thread: thread || undefined,
        body,
      });
      setThread(d.id);
      setBody("");
      void load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível enviar.");
    }
  }
  const current = threads.find((t) => t.id === thread);
  return (
    <section className="participant-tools adm-card">
      <h2>Suporte</h2>
      <select value={thread} onChange={(e) => setThread(e.target.value)}>
        <option value="">
          {admin ? "Selecione um atendimento" : "Nova solicitação"}
        </option>
        {threads.map((t) => (
          <option key={t.id} value={t.id}>
            {t.subject}
          </option>
        ))}
      </select>
      {current?.messages.map((m) => (
        <p key={m.id}>
          <strong>{m.author}</strong>: {m.body}
        </p>
      ))}
      <form onSubmit={send}>
        <label>
          {admin ? "Resposta" : "Como podemos ajudar?"}
          <textarea
            required
            maxLength={4000}
            value={body}
            onChange={(e) => setBody(e.target.value)}
          />
        </label>
        <button disabled={admin && !thread}>Enviar</button>
      </form>
      {error && <p role="alert">{error}</p>}
    </section>
  );
}

type Likes = {
  instructions: string;
  count: number;
  hidden: number;
  people: Person[];
  offers: {
    id: string;
    name: string;
    price: string;
    limit: number | null;
    durationMinutes: number | null;
  }[];
};
export function LikesReceived({ onPerson }: { onPerson: (p: Person) => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [data, setData] = useState<Likes | null>(null),
    [offers, setOffers] = useState(false),
    [message, setMessage] = useState("");
  const load = () =>
    request<Likes>("likes-received/")
      .then(setData)
      .catch((e) => setMessage(e.message));
  useEffect(() => {
    void load();
    const timer = setInterval(() => {
      if (!document.hidden) void load();
    }, 5000);
    return () => clearInterval(timer);
  }, []);
  return (
    <>
      <button
        onClick={() => {
          void load();
          dialog.current?.showModal();
        }}
      >
        Likes recebidos ({data?.count ?? 0})
      </button>
      <dialog ref={dialog} aria-label="Likes recebidos">
        <button
          onClick={() => dialog.current?.close()}
          aria-label="Fechar likes recebidos"
        >
          Fechar
        </button>
        <section className="participant-tools">
          <h2>Likes recebidos</h2>
          <p>Você recebeu {data?.count || 0} likes.</p>
          {!!data?.hidden && (
            <>
              <p>
                🔒 {data.hidden} identidades ocultas. Adquira um passe para
                revelar quem curtiu você.
              </p>
              <button onClick={() => setOffers(!offers)}>
                Adquirir novo passe
              </button>
            </>
          )}
          {data?.people.map((p) => (
            <button
              className="conversation-row"
              key={p.id}
              onClick={() => {
                dialog.current?.close();
                onPerson(p);
              }}
            >
              <img width={48} src={p.image} alt="" />
              {p.name}
            </button>
          ))}
          {offers && (
            <>
              <h3>Passes disponíveis</h3>
              {data?.offers.map((o) => (
                <article key={o.id}>
                  <h4>{o.name}</h4>
                  <p>
                    {o.limit
                      ? `${o.limit} revelações`
                      : `${o.durationMinutes} minutos`}{" "}
                    · R$ {o.price}
                  </p>
                  <button
                    onClick={() =>
                      setMessage(
                        data.instructions ||
                          "Procure o atendimento do evento para ativar este passe.",
                      )
                    }
                  >
                    Selecionar
                  </button>
                </article>
              ))}
            </>
          )}
          {message && <p role="status">{message}</p>}
        </section>
      </dialog>
    </>
  );
}
