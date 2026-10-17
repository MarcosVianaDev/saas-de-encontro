import { useState } from "react";
import type { Filters, ProfileTopic } from "../types";
import { topicSelections } from "../topic-filters";
import { Icon } from "./Icon";

export function TopicFilters({ topics, filters, onChange }: {
  topics: ProfileTopic[];
  filters: Filters;
  onChange: (filters: Filters) => void;
}) {
  const [searches, setSearches] = useState<Record<string, string>>({});
  return topics.map((topic) => {
    const selected = topicSelections(filters, topic);
    const search = searches[topic.key] || "";
    const options = topic.options.filter((option) => option.toLocaleLowerCase().includes(search.toLocaleLowerCase()));
    return <section className="filter-card" key={topic.id} aria-label={topic.name}>
      <div className="section-label"><h3>{topic.name}</h3><span>Opcional</span></div>
      <div className="search-field small">
        <Icon name="search" size={17} />
        <input aria-label={`Buscar opções de ${topic.name}`} placeholder="Buscar opções" value={search}
          onChange={(event) => setSearches({ ...searches, [topic.key]: event.target.value })} />
      </div>
      <div className="chips">
        <button type="button" className={`chip ${selected.length ? "" : "active"}`} aria-pressed={!selected.length}
          onClick={() => onChange({ ...filters, topics: { ...filters.topics, [topic.key]: [] },
            ...(topic.key === "interests" ? { interests: [] } : {}) })}>Não filtrar</button>
        {options.map((option) => <button type="button" key={option}
          className={`chip ${selected.includes(option) ? "active" : ""}`} aria-pressed={selected.includes(option)}
          onClick={() => {
            const values = selected.includes(option) ? selected.filter((value) => value !== option)
              : topic.filterMultiple ? [...selected, option] : [option];
            onChange({ ...filters, topics: { ...filters.topics, [topic.key]: values },
              ...(topic.key === "interests" ? { interests: values } : {}) });
          }}>{option}<Icon name={selected.includes(option) ? "check" : "plus"} size={13} /></button>)}
      </div>
      {!options.length && <p className="microcopy">Nenhuma opção encontrada.</p>}
      <p className="microcopy">{topic.filterMultiple ? "Mostrar pessoas com pelo menos uma das opções selecionadas." : "Selecione uma opção para filtrar."} “Não filtrar” inclui todas as opções.</p>
    </section>;
  });
}
