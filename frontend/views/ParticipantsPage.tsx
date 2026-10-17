import { useState } from "react";

import { brazilStateName } from "../brazil-states";

import { LikesReceived } from "../ParticipantExtras";

import { Icon } from "../components/Icon";
import { Avatar } from "../components/Avatar";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<
  ParticipantController,
  "chats" | "page" | "people" | "real" | "serverData" | "showDetails"
>;

export function ParticipantsPage({
  chats,
  page,
  people,
  real,
  serverData,
  showDetails,
}: Props) {
  const [participantSearch, setParticipantSearch] = useState("");
  const [tab, setTab] = useState("Todos");
  const [compact, setCompact] = useState(false);
  const shownParticipants = people.filter(
    (person) =>
      person.name
        .toLocaleLowerCase("pt-BR")
        .includes(participantSearch.toLocaleLowerCase("pt-BR")) &&
      (tab === "Todos" ||
        (tab === "Online" && person.online) ||
        (tab === "Matches" && person.id in chats)),
  );

  return (
    <>
      {page === "participantes" && (!real || serverData?.socialAvailable) && (
        <>
          <div className="screen-title">
            <h2>Participantes</h2>
            <LikesReceived mock={!real} onPerson={(p) => void showDetails(p)} />
            <button
              className="icon-button purple"
              aria-label={
                compact ? "Aumentar miniaturas" : "Diminuir miniaturas"
              }
              aria-pressed={compact}
              onClick={() => setCompact(!compact)}
            >
              <Icon name="grid" />
            </button>
          </div>
          <p className="subtitle">
            {people.length} pessoas, muitas possibilidades.
          </p>
          <div className="search-field">
            <Icon name="search" size={18} />
            <input
              aria-label="Buscar participantes"
              placeholder="Buscar participantes"
              value={participantSearch}
              onChange={(e) => setParticipantSearch(e.target.value)}
            />
          </div>
          <div
            className="participant-tabs"
            role="group"
            aria-label="Filtrar participantes"
          >
            {["Todos", "Online", "Matches"].map((item) => (
              <button
                className={`chip ${tab === item ? "active" : ""}`}
                aria-pressed={tab === item}
                key={item}
                onClick={() => setTab(item)}
              >
                {item}
              </button>
            ))}
          </div>
          <div className={`participants-grid ${compact ? "compact" : ""}`}>
            {shownParticipants.map((p) => (
              <button
                className="participant-tile"
                key={p.id}
                onClick={() => showDetails(p)}
              >
                <Avatar person={p} large />
                <strong>{p.name}</strong>
                <span>{p.age} anos</span>
                {p.residenceState && (
                  <span>{brazilStateName(p.residenceState)}</span>
                )}
                {p.id in chats && (
                  <span className="match-label">Seu match</span>
                )}
              </button>
            ))}
          </div>
          {!shownParticipants.length && (
            <div className="empty-state">
              <Icon name="search" size={32} />
              <h3>Ninguém por aqui</h3>
              <p>Tente outro nome ou outra categoria.</p>
            </div>
          )}
          <p className="participants-note">
            Todos os participantes validados, independentemente dos seus filtros
            de descoberta.
          </p>
        </>
      )}
    </>
  );
}
