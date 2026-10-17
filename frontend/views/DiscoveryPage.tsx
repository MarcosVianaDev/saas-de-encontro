import { CachedImage } from "../CachedImage";

import { brazilStateName } from "../brazil-states";
import { SocialSafety } from "../SocialSafety";

import { Icon } from "../components/Icon";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<
  ParticipantController,
  | "applyData"
  | "candidate"
  | "eligible"
  | "eventName"
  | "navigate"
  | "page"
  | "real"
  | "seen"
  | "select"
  | "serverData"
  | "setSeen"
  | "showDetails"
>;

export function DiscoveryPage({
  applyData,
  candidate,
  eligible,
  eventName,
  navigate,
  page,
  real,
  seen,
  select,
  serverData,
  setSeen,
  showDetails,
}: Props) {
  return (
    <>
      {page === "descobrir" && (
        <>
          <div className="screen-title">
            <h2>
              {serverData?.event.readOnly
                ? "A descoberta terminou"
                : "Descobrir pessoas"}
            </h2>
            {!serverData?.event.readOnly && (
              <button
                className="icon-button purple"
                aria-label="Alterar filtros"
                onClick={() => {
                  navigate("filtros");
                }}
              >
                <Icon name="filter" />
              </button>
            )}
          </div>
          {serverData?.event.readOnly && serverData.discoveryReport && (
            <section
              className="discovery-report"
              aria-label="Seu relatório do evento"
            >
              <ul>
                <li>
                  Você gostou de {serverData.discoveryReport.likesSent} pessoas.
                </li>
                <li>
                  {serverData.discoveryReport.likesReceived} pessoas gostaram de
                  você.
                </li>
                <li>Você deu {serverData.discoveryReport.matches} matches.</li>
                <li>
                  Conversou com {serverData.discoveryReport.conversations}{" "}
                  pessoas.
                </li>
              </ul>
            </section>
          )}
        </>
      )}
      {page === "descobrir" && (!real || serverData?.socialAvailable) && (
        <>
          <div className="discovery-meta">
            <span>
              <i className="live-dot" /> {eventName}
            </span>
            <span>
              {eligible.filter((p) => !seen.includes(p.id)).length} para
              descobrir
            </span>
          </div>
          {candidate ? (
            <>
              <div className="discovery-card">
                {real && (
                  <SocialSafety
                    person={candidate}
                    onChanged={(d) => applyData(d)}
                  />
                )}
                <CachedImage
                  src={candidate.image}
                  alt={`Retrato de ${candidate.name}`}
                  className="discovery-photo"
                />
                <span className="online-pill">
                  {candidate.online ? "● Online agora" : "No evento"}
                </span>
                <div className="card-person">
                  <div className="person-heading">
                    <h3>
                      {candidate.name}, {candidate.age}{" "}
                      <span className="verified" title="Participante validado">
                        <Icon name="check" size={13} />
                      </span>
                    </h3>
                    <button
                      className="info-button"
                      aria-label={`Ver perfil de ${candidate.name}`}
                      onClick={() => showDetails(candidate)}
                    >
                      i
                    </button>
                  </div>
                  {candidate.residenceState && (
                    <p>
                      <Icon name="pin" size={14} />
                      {brazilStateName(candidate.residenceState)}
                    </p>
                  )}
                  <div className="person-tags">
                    {candidate.interests.slice(0, 3).map((i) => (
                      <span key={i}>{i}</span>
                    ))}
                  </div>
                </div>
              </div>
              <div className="discovery-actions">
                <button
                  className="action-circle pass"
                  aria-label={`Passar ${candidate.name}`}
                  onClick={() => select(candidate, false)}
                >
                  <Icon name="close" size={32} />
                </button>
                <button
                  className="action-circle like"
                  aria-label={`Curtir ${candidate.name}`}
                  onClick={() => select(candidate, true)}
                >
                  <Icon name="heart" size={32} />
                </button>
              </div>
              <div className="actions-caption">
                <span>Passar</span>
                <span>Gostei</span>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <Icon name="search" size={34} />
              <h3>Você chegou ao fim por aqui.</h3>
              <p>
                Não há mais perfis com seus filtros atuais. Que tal revisar suas
                preferências?
              </p>
              <button
                className="primary"
                onClick={() => {
                  navigate("filtros");
                }}
              >
                Revisar filtros
              </button>
              <button
                className="text-button"
                onClick={() => {
                  if (!real) setSeen([]);
                }}
              >
                {real
                  ? "Histórico preservado no banco"
                  : "Rever perfis da demonstração"}
              </button>
            </div>
          )}
        </>
      )}
    </>
  );
}
