import { useState } from "react";

import { Icon } from "../components/Icon";
import { genderOptions, selectedGenders } from "../gender-filters";
import { TopicFilters } from "../components/TopicFilters";

import type { ParticipantController } from "../hooks/useParticipantController";

type Props = Pick<
  ParticipantController,
  "applyFilters" | "filters" | "eligibleFor" | "interests" | "purposes" | "filterTopics"
>;

export function FiltersPage({
  applyFilters,
  filters,
  eligibleFor,
  interests,
  purposes,
  filterTopics,
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
            <button type="button" className={`chip ${selectedGenders(draft).length === 0 ? "active" : ""}`}
              aria-pressed={selectedGenders(draft).length === 0}
              onClick={() => setDraft({ ...draft, gender: "Todos", genders: [] })}>Todos</button>
            {genderOptions.map((item) => (
              <button
                type="button"
                key={item.value}
                aria-pressed={selectedGenders(draft).includes(item.value)}
                className={`chip ${selectedGenders(draft).includes(item.value) ? "active" : ""}`}
                onClick={() => setDraft({ ...draft, gender: "Todos", genders: selectedGenders(draft).includes(item.value)
                  ? selectedGenders(draft).filter((gender) => gender !== item.value)
                  : [...selectedGenders(draft), item.value] })}
              >
                {item.label}
              </button>
            ))}
          </div>
          <p className="microcopy">Selecione um ou mais gêneros. Sem uma seleção específica, serão exibidos todos os gêneros.</p>
        </section>
        {filterTopics !== null ? <TopicFilters topics={filterTopics} filters={draft} onChange={setDraft} /> : <>
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
            <button type="button" className={`chip ${draft.interests.length ? "" : "active"}`}
              aria-pressed={!draft.interests.length} onClick={() => setDraft({ ...draft, interests: [] })}>Não filtrar</button>
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
            <button type="button" className={`chip ${draft.purpose ? "" : "active"}`}
              aria-pressed={!draft.purpose} onClick={() => setDraft({ ...draft, purpose: "" })}>Não filtrar</button>
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
        </>}
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
