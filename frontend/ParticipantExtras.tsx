import { CachedImage } from "./CachedImage";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { request } from "./backend-client";
import type { Person } from "./types";
import { FormattedText } from "./FormattedText";
import { createPortal } from "react-dom";
import { closeDialogOnBackdrop } from "./modal-backdrop";

export type Notice = {
  id: string;
  title: string;
  body: string;
  read: boolean;
  created: string;
  action: string;
  kind?: string;
  participant?: string | null;
};
const shownToastKey = "participant-shown-notification-ids";
function shownToastIds(): Set<string> {
  try {
    const ids: unknown = JSON.parse(
      localStorage.getItem(shownToastKey) || "[]",
    );
    return new Set(
      Array.isArray(ids)
        ? ids.filter((id): id is string => typeof id === "string")
        : [],
    );
  } catch {
    return new Set();
  }
}
function NotificationToast({
  notice,
  onOpen,
  onClose,
}: {
  notice: Notice;
  onOpen: (notice: Notice) => void;
  onClose: (id: string) => void;
}) {
  const close = useRef(onClose);
  const gesture = useRef<{ x: number; y: number; moved: boolean } | null>(null);
  const suppressClick = useRef(false);
  const [offset, setOffset] = useState(0);
  close.current = onClose;
  useEffect(() => {
    const timer = setTimeout(() => close.current(notice.id), 10000);
    return () => clearTimeout(timer);
  }, [notice.id]);
  return (
    <article
      className="toast notification-toast show"
      role="status"
      style={
        offset
          ? {
              transform: `translateX(${offset}px)`,
              opacity: Math.max(0.3, 1 - Math.abs(offset) / 350),
            }
          : undefined
      }
      onPointerDown={(e) => {
        if (!e.isPrimary || e.button !== 0) return;
        gesture.current = { x: e.clientX, y: e.clientY, moved: false };
        suppressClick.current = false;
      }}
      onPointerMove={(e) => {
        const start = gesture.current;
        if (!start) return;
        const x = e.clientX - start.x;
        const y = e.clientY - start.y;
        if (!start.moved && Math.abs(y) > Math.max(8, Math.abs(x))) {
          gesture.current = null;
          return;
        }
        if (Math.abs(x) > 8 && Math.abs(x) > Math.abs(y)) {
          start.moved = true;
          suppressClick.current = true;
          e.currentTarget.setPointerCapture(e.pointerId);
        }
        if (start.moved) setOffset(x);
      }}
      onPointerUp={(e) => {
        const start = gesture.current;
        gesture.current = null;
        setOffset(0);
        if (start?.moved && Math.abs(e.clientX - start.x) >= 60)
          onClose(notice.id);
      }}
      onPointerCancel={() => {
        gesture.current = null;
        setOffset(0);
      }}
      onClickCapture={(e) => {
        if (suppressClick.current && e.detail > 0) {
          e.preventDefault();
          e.stopPropagation();
        }
      }}
    >
      <div className="toast-header">
        <strong>{notice.title}</strong>
        <button
          className="btn-close"
          aria-label="Fechar notificação"
          onClick={() => onClose(notice.id)}
        >
          ×
        </button>
      </div>
      <button
        className="toast-body"
        onClick={() => {
          onClose(notice.id);
          onOpen(notice);
        }}
      >
        {notice.body || "Abrir notificação"}
        <span>Abrir</span>
      </button>
    </article>
  );
}
export function NotificationCenter({
  visible,
  onUnread,
  onOpen,
}: {
  visible: boolean;
  onUnread: (count: number) => void;
  onOpen?: (notice: Notice) => void;
}) {
  const seen = useRef<Set<string> | null>(null);
  if (seen.current === null) seen.current = shownToastIds();
  const [toasts, setToasts] = useState<Notice[]>([]);
  const dismiss = (id: string) =>
    setToasts((old) => old.filter((n) => n.id !== id));
  const [items, setItems] = useState<Notice[]>([]),
    [error, setError] = useState("");
  const load = () =>
    request<{ unread: number; items: Notice[] }>("notifications/")
      .then((d) => {
        setItems(d.items);
        onUnread(d.unread);
        const fresh = d.items.filter(
          (notice) => !seen.current!.has(notice.id) && !notice.read,
        );
        if (onOpen && fresh.length) {
          const shown = fresh.slice(0, 3);
          shown.forEach((notice) => seen.current!.add(notice.id));
          try {
            const stored = shownToastIds();
            seen.current!.forEach((id) => stored.add(id));
            seen.current = stored;
            localStorage.setItem(shownToastKey, JSON.stringify([...stored]));
          } catch {
            // Keep session deduplication when local storage is unavailable.
          }
          setToasts((old) => [...shown, ...old].slice(0, 3));
        }
      })
      .catch((e) => setError(e.message));
  const activate = async (notice: Notice) => {
    try {
      await request("notifications/", "POST", { id: notice.id });
      setItems((old) =>
        old.map((item) =>
          item.id === notice.id ? { ...item, read: true } : item,
        ),
      );
      dismiss(notice.id);
      void load();
      if (onOpen) onOpen(notice);
      else if (notice.action.startsWith("#")) location.hash = notice.action;
      else if (/^https?:\/\//.test(notice.action))
        location.assign(notice.action);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Não foi possível abrir a notificação.",
      );
    }
  };
  useEffect(() => {
    void load();
    const t = setInterval(() => {
      if (!document.hidden) void load();
    }, 5000);
    return () => clearInterval(t);
  }, []);
  return (
    <>
      {onOpen &&
        createPortal(
          <div
            className="toast-container notification-toast-container"
            aria-live="polite"
          >
            {toasts.map((notice) => (
              <NotificationToast
                key={notice.id}
                notice={notice}
                onOpen={(notice) => void activate(notice)}
                onClose={dismiss}
              />
            ))}
          </div>,
          document.body,
        )}
      {visible && (
        <section className="participant-tools">
          <h2>Notificações</h2>
          {error && <p role="alert">{error}</p>}
          {!items.length && <p>Nenhuma notificação.</p>}
          {items.map((n) => (
            <article
              key={n.id}
              className={`notification-card ${n.read ? "" : "unread"}`}
              role="button"
              tabIndex={0}
              aria-label={n.title}
              onClick={() => void activate(n)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  void activate(n);
                }
              }}
            >
              <h3>{n.title}</h3>
              <p>
                <FormattedText text={n.body} />
              </p>
              <small>{new Date(n.created).toLocaleString("pt-BR")}</small>
              <span className="notification-read-status">
                {n.read ? "Lida" : "Não lida"}
              </span>
            </article>
          ))}
        </section>
      )}
    </>
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
      <dialog
        ref={dialog}
        aria-label="Likes recebidos"
        onClick={(e) => closeDialogOnBackdrop(e, () => dialog.current?.close())}
      >
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
              <CachedImage width={48} src={p.image} alt="" />
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
