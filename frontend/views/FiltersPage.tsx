import { useState } from "react";

import { Icon } from "../components/Icon";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<
  ParticipantController,
  "applyFilters" | "filters" | "eligibleFor" | "interests" | "purposes"
>;

export function FiltersPage({
  applyFilters,
  filters,
  eligibleFor,
  interests,
  purposes,
}: Props) {
  const [draft, setDraft] = useState(filters);
  const [interestSearch, setInterestSearch] = useState("");

  return (
    <>
      <form
        id="filters-form"
        className="filters-form"
        onSubmit={(event) => {
          event.preventDefault();
          void applyFilters(draft);
        }}
      >
        <h2>Definir filtros</h2>
        <p className="subtitle">
          Personalize suas preferências para
          <br />
          encontrar pessoas que combinam com você.
        </p>
        <section className="filter-card">
          <h3>Faixa etária</h3>
          <div className="range-value">
            {draft.min} a {draft.max} anos
          </div>
          <div className="range-inputs">
            <label>
              De
              <input
                aria-label="Idade mínima"
                type="range"
                min="18"
                max="70"
                value={draft.min}
                onChange={(e) =>
                  setDraft({
                    ...draft,
                    min: Math.min(Number(e.target.value), draft.max),
                  })
                }
              />
            </label>
            <label>
              Até
              <input
                aria-label="Idade máxima"
                type="range"
                min="18"
                max="100"
                value={draft.max}
                onChange={(e) =>
                  setDraft({
                    ...draft,
                    max: Math.max(Number(e.target.value), draft.min),
                  })
                }
              />
            </label>
          </div>
        </section>
        <section className="filter-card">
          <div className="section-label"><h3>Altura</h3><span>Opcional</span></div>
          <div className="form-row">
            <label className="field">
              <span>Altura mínima (cm)</span>
              <input type="number" inputMode="numeric" min={50} max={draft.maxHeight ?? 250} step={1}
                placeholder="Sem mínimo" value={draft.minHeight ?? ""}
                onChange={(event) => setDraft({ ...draft, minHeight: event.target.value === "" ? null : Number(event.target.value) })} />
            </label>
            <label className="field">
              <span>Altura máxima (cm)</span>
              <input type="number" inputMode="numeric" min={draft.minHeight ?? 50} max={250} step={1}
                placeholder="Sem máximo" value={draft.maxHeight ?? ""}
                onChange={(event) => setDraft({ ...draft, maxHeight: event.target.value === "" ? null : Number(event.target.value) })} />
            </label>
          </div>
          <p className="microcopy">Ao definir uma altura, somente participantes com altura informada dentro da faixa serão exibidos.</p>
        </section>
        <section className="filter-card">
          <h3>Gênero</h3>
          <div className="chips">
            {["Todos", "Mulheres", "Homens"].map((item) => (
              <button
                type="button"
                key={item}
                aria-pressed={draft.gender === item}
                className={`chip ${draft.gender === item ? "active" : ""}`}
                onClick={() => setDraft({ ...draft, gender: item })}
              >
                {item}
              </button>
            ))}
          </div>
        </section>
        <section className="filter-card">
          <div className="section-label">
            <h3>Interesses</h3>
            <span>Opcional</span>
          </div>
          <div className="search-field small">
            <Icon name="search" size={17} />
            <input
              aria-label="Buscar interesses"
              placeholder="Buscar interesses"
              value={interestSearch}
              onChange={(e) => setInterestSearch(e.target.value)}
            />
          </div>
          <div className="chips">
            {interests
              .filter((item) =>
                item.toLowerCase().includes(interestSearch.toLowerCase()),
              )
              .map((item) => (
                <button
                  type="button"
                  key={item}
                  aria-pressed={draft.interests.includes(item)}
                  className={`chip ${draft.interests.includes(item) ? "active" : ""}`}
                  onClick={() =>
                    setDraft({
                      ...draft,
                      interests: draft.interests.includes(item)
                        ? draft.interests.filter((i) => i !== item)
                        : [...draft.interests, item],
                    })
                  }
                >
                  {item}
                  <Icon
                    name={draft.interests.includes(item) ? "check" : "plus"}
                    size={13}
                  />
                </button>
              ))}
          </div>
          {!interests.some((item) =>
            item.toLowerCase().includes(interestSearch.toLowerCase()),
          ) && <p className="microcopy">Nenhum interesse encontrado.</p>}
          <p className="microcopy">
            Mostrar pessoas com pelo menos um interesse selecionado.
          </p>
        </section>
        <section className="filter-card">
          <h3>Finalidade no evento</h3>
          <div className="chips">
            {purposes.map((item) => (
              <button
                type="button"
                key={item}
                aria-pressed={draft.purpose === item}
                className={`chip ${draft.purpose === item ? "active" : ""}`}
                onClick={() => setDraft({ ...draft, purpose: item })}
              >
                {item}
              </button>
            ))}
          </div>
          <p className="microcopy">
            Uma preferência para apresentar no seu perfil.
          </p>
        </section>
        <div className="filter-summary">
          <Icon name="people" size={18} />
          <span>
            {eligibleFor(draft).length} pessoas combinam com seus filtros
          </span>
        </div>
      </form>
    </>
  );
}
