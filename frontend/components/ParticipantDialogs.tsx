import { useEffect } from "react";

import { ProfileGallery } from "../ProfileGallery";
import { CachedImage } from "../CachedImage";

import { brazilStateName } from "../brazil-states";
import { SocialSafety } from "../SocialSafety";

import { Icon } from "../components/Icon";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<
  ParticipantController,
  | "applyData"
  | "chats"
  | "details"
  | "liked"
  | "match"
  | "openChat"
  | "photos"
  | "real"
  | "select"
  | "setDetails"
  | "setMatch"
>;

export function ParticipantDialogs({
  applyData,
  chats,
  details,
  liked,
  match,
  openChat,
  photos,
  real,
  select,
  setDetails,
  setMatch,
}: Props) {
  useEffect(() => {
    const esc = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setDetails(null);
        setMatch(null);
      }
    };
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, []);
  useEffect(() => {
    if (!details && !match) return;
    const previous = document.activeElement as HTMLElement | null;
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]');
    const trap = (event: KeyboardEvent) => {
      if (event.key !== "Tab" || !dialog) return;
      const buttons = Array.from(
        dialog.querySelectorAll<HTMLElement>(
          "button:not(:disabled), input, a[href]",
        ),
      );
      const first = buttons[0];
      const last = buttons.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", trap);
    return () => {
      document.removeEventListener("keydown", trap);
      if (previous?.isConnected) previous.focus();
    };
  }, [details, match]);

  return (
    <>
      {details && (
        <div className="modal-backdrop" onClick={() => setDetails(null)}>
          <section
            role="dialog"
            aria-modal="true"
            aria-label={`Perfil de ${details.name}`}
            className="person-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              autoFocus
              className="modal-close"
              aria-label="Fechar perfil"
              onClick={() => setDetails(null)}
            >
              <Icon name="close" />
            </button>
            <div className="person-modal-content">
              <ProfileGallery key={String(details.id)} person={details} />
              <div className="modal-body">
                <h2>
                  {details.name}, {details.age}{" "}
                  <span className="verified">
                    <Icon name="check" size={13} />
                  </span>
                </h2>
                {details.residenceState && (
                  <p className="modal-location">
                    <Icon name="pin" size={15} />
                    {brazilStateName(details.residenceState)}
                  </p>
                )}
                {(details.bio || !real) && (
                  <p>
                    {details.bio ||
                      "Gosto de boas conversas, novas experiências e pessoas que têm histórias para contar. Vamos nos conhecer?"}
                  </p>
                )}
                <div className="chips">
                  {details.interests.slice(0, 3).map((item) => (
                    <span className="chip" key={item}>
                      {item}
                    </span>
                  ))}
                </div>
                <p className="microcopy">
                  {details.id in chats
                    ? "Vocês já deram match. Que tal começar uma conversa?"
                    : "As fotos adicionais e o chat são liberados após um match."}
                </p>
                {details.id in chats ? (
                  <button
                    className="primary"
                    onClick={() => openChat(details.id)}
                  >
                    Enviar mensagem <Icon name="chat" size={18} />
                  </button>
                ) : (
                  <button
                    className="primary"
                    disabled={liked.includes(details.id)}
                    onClick={() => {
                      select(details, true);
                      setDetails(null);
                    }}
                  >
                    {liked.includes(details.id) ? "Like enviado" : "Gostei"}{" "}
                    <Icon name="heart" size={18} />
                  </button>
                )}
                {real && (
                  <SocialSafety
                    person={details}
                    allowBlock
                    onChanged={(d) => applyData(d)}
                  />
                )}
              </div>
            </div>
          </section>
        </div>
      )}
      {match && (
        <div
          className="modal-backdrop"
          onClick={(e) => {
            if (e.target === e.currentTarget) setMatch(null);
          }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-label="Novo match"
            className="match-modal"
          >
            <button
              autoFocus
              className="modal-close"
              aria-label="Fechar match"
              onClick={() => setMatch(null)}
            >
              <Icon name="close" />
            </button>
            <span className="match-spark">✦</span>
            <h2>Deu match!</h2>
            <p>
              A conexão é mútua.
              <br />
              Que tal dar o primeiro oi?
            </p>
            <div className="match-avatars">
              <CachedImage
                src={photos[0] || "/images/profile-placeholder.svg"}
                alt="Seu perfil"
              />
              <span>
                <Icon name="heart" size={26} />
              </span>
              <CachedImage src={match.image} alt={match.name} />
            </div>
            <strong>Você e {match.name}</strong>
            <button
              className="primary"
              onClick={() => {
                openChat(match.id);
                setMatch(null);
              }}
            >
              Começar conversa <Icon name="chat" size={19} />
            </button>
            <button className="text-button" onClick={() => setMatch(null)}>
              Continuar descobrindo
            </button>
          </section>
        </div>
      )}
    </>
  );
}
