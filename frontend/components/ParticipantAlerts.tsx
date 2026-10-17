import { useRef } from "react";

import { request } from "../backend-client";

import { closeDialogOnBackdrop } from "../modal-backdrop";

import type { Bootstrap } from "../types";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<
  ParticipantController,
  | "applyData"
  | "busy"
  | "navigate"
  | "notify"
  | "page"
  | "run"
  | "serverData"
  | "setMailbox"
>;

export function ParticipantAlerts({
  applyData,
  busy,
  navigate,
  notify,
  page,
  run,
  serverData,
  setMailbox,
}: Props) {
  const deletionDialog = useRef<HTMLDialogElement>(null);
  if (!serverData) return null;

  return (
    <>
      <div className="participant-alerts">
        {serverData.event.endingSoon && !serverData.event.readOnly && (
          <p className="event-banner alert alert-warning" role="alert">
            O evento encerra às{" "}
            {serverData.event.ends
              ? new Date(serverData.event.ends).toLocaleTimeString("pt-BR", {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : ""}
            .
          </p>
        )}
        {serverData.event.state === "PAUSED" && (
          <section className="event-banner alert alert-warning" role="alert">
            <strong>Evento pausado pela organização</strong>
            <p>
              Novas descobertas estão temporariamente indisponíveis. Suas
              conversas e matches continuam acessíveis.
            </p>
            <button onClick={() => navigate("mensagens")}>
              Ir para mensagens
            </button>
          </section>
        )}
        {serverData.event.state === "OPEN" && (
          <section className="event-banner alert alert-info" role="status">
            <strong>O evento ainda não começou</strong>
            <p>
              A descoberta de participantes será liberada quando o evento
              começar.
            </p>
            <button onClick={() => navigate("perfil")}>Ver meu perfil</button>
          </section>
        )}
        {serverData.event.readOnly && (
          <section className="event-banner alert alert-warning" role="alert">
            <strong>Este evento foi encerrado</strong>
            <p>Perfil e conversas estão disponíveis somente para consulta.</p>
            {page === "perfil" && (
              <>
                <h3>O que deseja fazer com seu perfil?</h3>
                <div className="profile-disposition-actions">
                  <button
                    className="soft-success"
                    disabled={busy}
                    onClick={() =>
                      void run(async () => {
                        applyData(
                          await request<Bootstrap>(
                            "profile/disposition/",
                            "POST",
                            { action: "persist" },
                          ),
                        );
                        notify("Perfil salvo para futuros eventos.");
                      })
                    }
                  >
                    Salvar perfil para futuros eventos
                  </button>
                  <button
                    className="soft-danger"
                    disabled={busy}
                    onClick={() => deletionDialog.current?.showModal()}
                  >
                    Descartar perfil deste evento
                  </button>
                </div>
                <dialog
                  ref={deletionDialog}
                  className="disposition-dialog"
                  aria-label="Descartar perfil deste evento"
                  onClick={(e) =>
                    closeDialogOnBackdrop(e, () =>
                      deletionDialog.current?.close(),
                    )
                  }
                >
                  <h2>Descartar perfil deste evento</h2>
                  <p>
                    Seu perfil deixará de aparecer socialmente. Dados sujeitos a
                    obrigações legais, segurança ou preservação poderão
                    permanecer pelo período aplicável.
                  </p>
                  <button
                    className="soft-secondary"
                    onClick={() => deletionDialog.current?.close()}
                  >
                    Cancelar
                  </button>
                  <button
                    className="soft-danger"
                    disabled={busy}
                    onClick={() =>
                      void run(async () => {
                        const updated = await request<Bootstrap>(
                          "profile/disposition/",
                          "POST",
                          { action: "delete", confirmed: true },
                        );
                        deletionDialog.current?.close();
                        applyData(updated);
                        notify("Exposição social removida.");
                      })
                    }
                  >
                    Descartar
                  </button>
                </dialog>
              </>
            )}
          </section>
        )}
        {serverData.registrationStatus === "PENDING" && (
          <p className="event-banner alert alert-warning" role="alert">
            Aguardando ativação. Procure a equipe para capturar a foto do look e
            validar seu perfil.
          </p>
        )}
        {serverData.registrationStatus === "INACTIVE" && (
          <p className="event-banner alert alert-warning" role="alert">
            Seu perfil está temporariamente desativado ou em análise. Você pode
            falar com o Suporte em Mensagens.
            <button
              onClick={() => {
                navigate("mensagens");
                setMailbox("support");
              }}
            >
              Falar com o suporte
            </button>
          </p>
        )}
        {page === "descobrir" &&
          !serverData.socialAvailable &&
          ["OPEN", "RUNNING", "PAUSED"].includes(
            serverData.event.state || "",
          ) && (
            <p className="event-banner alert alert-warning" role="alert">
              Você já pode definir suas preferências nos filtros. A descoberta
              de pessoas estará disponível após a ativação do perfil e quando o
              evento estiver em andamento.
            </p>
          )}
      </div>
    </>
  );
}
