import { CachedImage } from "../CachedImage";

import { Icon } from "../components/Icon";

import { stages } from "../participant-pages";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<ParticipantController, "page" | "people" | "stage">;

export function DemoContext({ page, people, stage }: Props) {
  return (
    <>
      <aside className="context-panel">
        <span className="eyebrow">
          {String(stage + 1).padStart(2, "0")} / A SUA EXPERIÊNCIA
        </span>
        <h2>
          {[
            "Toda conexão tem|um começo.",
            "Seja você.|É o melhor jeito.",
            "Sua vibe.|Suas conexões.",
            "O próximo encontro|pode estar aqui.",
            "Um match.|Muitas histórias.",
            "Gente interessante.|No mesmo lugar.",
          ][stage]
            .split("|")
            .map((line, i) => (
              <span key={line}>
                {line}
                {i === 0 && <br />}
              </span>
            ))}
        </h2>
        <p>
          {stages[stage].description} Descubra uma experiência feita para
          aproximar pessoas no mundo real.
        </p>
        <div className="event-preview">
          <span className="event-art">
            <Icon name="people" size={32} />
            <span>
              conecta<span>2026</span>
            </span>
          </span>
          <div>
            <small>VOCÊ ESTÁ EM</small>
            <strong>Conecta São Paulo</strong>
            <span>
              <Icon name="pin" size={13} /> São Paulo · edição 2026
            </span>
          </div>
        </div>
        <div className="community">
          <div className="avatar-stack">
            {people.slice(0, 4).map((p) => (
              <CachedImage key={p.id} src={p.image} alt="" />
            ))}
          </div>
          <span>
            <strong>{people.length} pessoas</strong> prontas para se conectar
          </span>
        </div>
        <div className="context-tip">
          <span>✦</span>
          <p>
            {page === "perfil"
              ? "Um perfil completo faz toda a diferença. Escolha fotos que contem a sua história."
              : page === "filtros"
                ? "Seus filtros podem mudar junto com você. Ajuste quando quiser."
                : "As melhores conexões começam quando você se permite conhecer alguém novo."}
          </p>
        </div>
        <span className="context-footnote">
          Demonstração visual · dados fictícios
        </span>
      </aside>
    </>
  );
}
