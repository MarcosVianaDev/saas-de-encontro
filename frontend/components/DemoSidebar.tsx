import { Icon } from "../components/Icon";

import { stages } from "../participant-pages";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<ParticipantController, "navigate" | "page">;

export function DemoSidebar({ navigate, page }: Props) {
  return (
    <>
      <aside className="sidebar">
        <a className="brand" href="#login">
          <span className="brand-icon">
            <Icon name="people" size={28} />
          </span>
          <span>
            Event<span className="brand-accent">Connect</span>
          </span>
        </a>
        <div className="event-label">
          <i className="live-dot" /> CONEXÕES QUE ACONTECEM
        </div>
        <h1>
          Pessoas reais.
          <br />
          <span>Encontros incríveis.</span>
        </h1>
        <p className="sidebar-intro">
          Encontre quem combina com você e aproveite cada momento do evento.
        </p>
        <nav className="stage-nav" aria-label="Etapas da experiência">
          {stages.map((s, index) => (
            <button
              key={s.page}
              className={page === s.page ? "selected" : ""}
              onClick={() => navigate(s.page)}
              aria-current={page === s.page ? "page" : undefined}
            >
              <span className="stage-number">{index + 1}</span>
              <span>
                {s.title}
                <small>{s.description}</small>
              </span>
              {page === s.page && <i className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="preview-badge">PRÉVIA INTERATIVA</span>
          <p>Dados de exemplo para explorar a experiência.</p>
          <span>Feito para conectar. 💜</span>
        </div>
      </aside>
    </>
  );
}
