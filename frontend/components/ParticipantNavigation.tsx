import { Icon, type IconName } from "../components/Icon";

import { type Page } from "../participant-pages";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<
  ParticipantController,
  "navigateBottom" | "noticeUnread" | "page" | "unread"
>;

export function ParticipantNavigation({
  navigateBottom,
  noticeUnread,
  page,
  unread,
}: Props) {
  return (
    <>
      <nav className="bottom-nav" aria-label="Navegação principal">
        {(
          [
            {
              page: "descobrir",
              text: "Descobrir",
              icon: "search",
            },
            { page: "mensagens", text: "Mensagens", icon: "chat" },
            {
              page: "participantes",
              text: "Participantes",
              icon: "people",
            },
            { page: "perfil", text: "Perfil", icon: "user" },
          ] as { page: Page; text: string; icon: IconName }[]
        ).map((item) => (
          <button
            key={item.page}
            className={
              page === item.page ||
              (page === "filtros" && item.page === "descobrir")
                ? "active"
                : ""
            }
            onClick={() => navigateBottom(item.page)}
            aria-current={
              page === item.page ||
              (page === "filtros" && item.page === "descobrir")
                ? "page"
                : undefined
            }
          >
            <Icon name={item.icon} size={22} />
            <span>{item.text}</span>
            {item.page === "mensagens" &&
              (unread.length > 0 || noticeUnread > 0) && (
                <i className="nav-unread" />
              )}
          </button>
        ))}
      </nav>
    </>
  );
}
