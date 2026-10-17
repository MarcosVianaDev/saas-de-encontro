import { NotificationCenter, SupportPanel } from "../ParticipantExtras";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<
  ParticipantController,
  | "authenticated"
  | "mailbox"
  | "noticeUnread"
  | "openNotification"
  | "page"
  | "real"
  | "serverData"
  | "setMailbox"
  | "setNoticeUnread"
>;

export function ParticipantMailbox({
  authenticated,
  mailbox,
  noticeUnread,
  openNotification,
  page,
  real,
  serverData,
  setMailbox,
  setNoticeUnread,
}: Props) {
  return (
    <>
      {authenticated && (serverData || !real) && (
        <>
          {page === "mensagens" && (
            <nav
              className="mailbox-tabs nav nav-tabs"
              aria-label="Seções de mensagens"
            >
              <button
                className={`nav-link ${mailbox === "messages" ? "active" : ""}`}
                aria-current={mailbox === "messages" ? "page" : undefined}
                onClick={() => setMailbox("messages")}
              >
                Mensagens
              </button>
              <button
                className={`nav-link ${mailbox === "notifications" ? "active" : ""}`}
                aria-current={mailbox === "notifications" ? "page" : undefined}
                onClick={() => setMailbox("notifications")}
              >
                Notificações {noticeUnread > 0 ? `(${noticeUnread})` : ""}
              </button>
              <button
                className={`nav-link ${mailbox === "support" ? "active" : ""}`}
                aria-current={mailbox === "support" ? "page" : undefined}
                onClick={() => setMailbox("support")}
              >
                Suporte
              </button>
            </nav>
          )}
          <NotificationCenter
            mock={!real}
            visible={page === "mensagens" && mailbox === "notifications"}
            onUnread={setNoticeUnread}
            onOpen={openNotification}
          />
          {page === "mensagens" && mailbox === "support" && (
            <SupportPanel mock={!real} />
          )}
        </>
      )}
    </>
  );
}
