import { useEffect, useRef, useState, type FormEvent } from "react";

import { api } from "../backend-client";

import { SocialSafety } from "../SocialSafety";

import { Icon } from "../components/Icon";
import { Avatar } from "../components/Avatar";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<
  ParticipantController,
  | "activeChat"
  | "applyData"
  | "busy"
  | "chatStates"
  | "chats"
  | "mailbox"
  | "notify"
  | "openChat"
  | "page"
  | "people"
  | "real"
  | "run"
  | "saved"
  | "send"
  | "serverData"
  | "setActiveChat"
  | "showDetails"
  | "toggleFavorite"
  | "unread"
>;

export function MessagesPage({
  activeChat,
  applyData,
  busy,
  chatStates,
  chats,
  mailbox,
  notify,
  openChat,
  page,
  people,
  real,
  run,
  saved,
  send,
  serverData,
  setActiveChat,
  showDetails,
  toggleFavorite,
  unread,
}: Props) {
  const [message, setMessage] = useState("");
  const [chatSearch, setChatSearch] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "nearest" });
  }, [activeChat, chats]);

  const submitMessage = async (event: FormEvent) => {
    event.preventDefault();
    const text = message;
    if (await send(text))
      setMessage((current) => (current === text ? "" : current));
  };

  return (
    <>
      {page === "mensagens" &&
        mailbox === "messages" &&
        (activeChat === null ? (
          <>
            <div className="screen-title">
              <h2>Mensagens</h2>
              <span className="count-badge">{Object.keys(chats).length}</span>
            </div>
            <p className="subtitle">Boas histórias começam com um oi.</p>
            <div className="search-field">
              <Icon name="search" size={18} />
              <input
                aria-label="Buscar conversas"
                placeholder="Buscar conversas"
                value={chatSearch}
                onChange={(e) => setChatSearch(e.target.value)}
              />
            </div>
            <div className="conversation-list">
              {people
                .filter(
                  (p) =>
                    p.id in chats &&
                    p.name.toLowerCase().includes(chatSearch.toLowerCase()),
                )
                .map((p) => {
                  const last = chats[p.id].at(-1);
                  return (
                    <button
                      className="conversation-row"
                      key={p.id}
                      onClick={() => openChat(p.id)}
                    >
                      <Avatar person={p} />
                      <span className="conversation-info">
                        <strong>{p.name}</strong>
                        <span>
                          {last
                            ? `${last.mine ? "Você: " : ""}${last.text}`
                            : "Vocês combinaram! Envie um oi 💜"}
                        </span>
                      </span>
                      <span className="conversation-time">
                        {last?.time || "Agora"}
                        {unread.includes(p.id) && <i>1</i>}
                      </span>
                    </button>
                  );
                })}
            </div>
            {!people.some(
              (p) =>
                p.id in chats &&
                p.name.toLowerCase().includes(chatSearch.toLowerCase()),
            ) && (
              <div className="empty-state">
                <Icon name="chat" size={32} />
                <h3>Nenhuma conversa encontrada</h3>
                <p>Os seus matches aparecem aqui.</p>
              </div>
            )}
            <div className="safe-chat">
              <Icon name="heart" size={15} /> Conversas liberadas quando o
              interesse é mútuo.
            </div>
          </>
        ) : (
          <>
            <div className="chat-heading">
              <button
                className="icon-button"
                aria-label="Voltar às conversas"
                onClick={() => setActiveChat(null)}
              >
                <Icon name="back" />
              </button>
              <details
                className="chat-participant-menu"
                key={String(activeChat)}
              >
                <summary
                  className="chat-participant-card"
                  aria-label="Opções do participante"
                >
                  <Avatar person={people.find((p) => p.id === activeChat)!} />
                  <span className="chat-participant-info">
                    <strong>
                      {people.find((p) => p.id === activeChat)!.name}
                      {people.find((p) => p.id === activeChat)!.age != null &&
                        `, ${people.find((p) => p.id === activeChat)!.age}`}
                    </strong>
                    <span>
                      {people.find((p) => p.id === activeChat)!.online
                        ? "Online agora"
                        : "Participante do evento"}
                    </span>
                  </span>
                </summary>
                <div className="chat-participant-dropdown">
                  <button
                    onClick={() =>
                      void showDetails(people.find((p) => p.id === activeChat)!)
                    }
                  >
                    Ver perfil
                  </button>
                  {chatStates[String(activeChat)]?.active && (
                    <button
                      onClick={() =>
                        void toggleFavorite(
                          people.find((p) => p.id === activeChat)!,
                        )
                      }
                    >
                      {saved.includes(activeChat)
                        ? "Desfavoritar"
                        : "Favoritar"}
                    </button>
                  )}
                  <SocialSafety
                    person={people.find((p) => p.id === activeChat)!}
                    allowBlock
                    onChanged={(d) => applyData(d)}
                  />
                </div>
              </details>
              {real && chatStates[String(activeChat)]?.active && (
                <button
                  className="secondary end-match"
                  disabled={busy}
                  onClick={() =>
                    void run(async () => {
                      applyData(await api.endMatch(activeChat!));
                      notify("Match encerrado. Histórico preservado.");
                    })
                  }
                >
                  Encerrar match
                </button>
              )}
            </div>
            <div className="message-history">
              <span className="day-divider">Hoje</span>
              <p className="match-note">
                {real && chatStates[String(activeChat)]?.active === false
                  ? "Match encerrado. Histórico em modo somente leitura."
                  : "Vocês deram match. A conversa começa aqui. 💜"}
              </p>
              {chats[activeChat]?.map((entry, index) => (
                <div
                  key={index}
                  className={`message-bubble ${entry.mine ? "mine" : ""}`}
                >
                  <p>{entry.text}</p>
                  <span>
                    {entry.time}
                    {entry.mine && " ✓"}
                  </span>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
            {real && serverData?.event.readOnly ? (
              <p>
                Este evento terminou. A conversa está disponível somente para
                consulta.
              </p>
            ) : (
              <form className="message-composer" onSubmit={submitMessage}>
                <input
                  aria-label="Mensagem"
                  disabled={
                    real &&
                    activeChat !== null &&
                    chatStates[String(activeChat)]?.active === false
                  }
                  placeholder={
                    real &&
                    activeChat !== null &&
                    chatStates[String(activeChat)]?.active === false
                      ? "Conversa em modo somente leitura"
                      : "Escreva sua mensagem…"
                  }
                  value={message}
                  maxLength={2000}
                  onChange={(e) => setMessage(e.target.value)}
                />
                <button
                  className="send-button"
                  aria-label="Enviar mensagem"
                  disabled={
                    !message.trim() ||
                    busy ||
                    (real &&
                      activeChat !== null &&
                      chatStates[String(activeChat)]?.active === false)
                  }
                >
                  <Icon name="send" size={20} />
                </button>
              </form>
            )}
          </>
        ))}
    </>
  );
}
