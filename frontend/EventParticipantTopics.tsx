import { useState } from "react";
import Accordion from "react-bootstrap/Accordion";
import type { ProfileTopic } from "./types";

export type EventTopicRule = { topic: string; enabled: boolean; required: boolean; minimum: number };

export function EventParticipantTopics({ topics, rules, onChange }: {
  topics: ProfileTopic[];
  rules: EventTopicRule[];
  onChange: (rules: EventTopicRule[]) => void;
}) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const update = (id: string, values: Partial<EventTopicRule>) => onChange(rules.map((rule) => rule.topic === id ? { ...rule, ...values } : rule));
  return (
    <Accordion>
      <Accordion.Item eventKey="topics">
        <Accordion.Header>Tópicos do participante</Accordion.Header>
        <Accordion.Body>
          {!topics.length && <p>Nenhum tópico cadastrado.</p>}
          {topics.map((topic) => {
            const rule = rules.find((item) => item.topic === topic.id);
            if (!rule) return null;
            const open = expanded === topic.id;
            const showMinimum = topic.multiple && rule.required;
            const maximum = topic.multiple ? Math.min(5, topic.options.length) : 1;
            return (
              <div className="event-topic-card" key={topic.id} onClick={(e) => {
                if ((e.target as HTMLElement).closest("button, label, input")) return;
                setExpanded(open ? null : topic.id);
              }}>
                <div className="event-topic-row">
                  <label className="event-topic-use">
                    <span>Usar no evento</span>
                    <input type="checkbox" role="switch" className="app-toggle" checked={rule.enabled} onChange={(e) => update(topic.id, { enabled: e.target.checked, ...(!e.target.checked ? { required: false, minimum: 1 } : {}) })} />
                  </label>
                  <button type="button" className="event-topic-expand" aria-expanded={open} aria-controls={`topic-options-${topic.id}`} onClick={() => setExpanded(open ? null : topic.id)}>
                    <strong>{topic.name}</strong><span aria-hidden="true">{open ? "−" : "+"}</span>
                  </button>
                  <div className="event-topic-requirement">
                  <label>
                    <span>Obrigatório</span>
                    <input type="checkbox" role="switch" className="app-toggle" checked={rule.required} disabled={!rule.enabled} onChange={(e) => { update(topic.id, { required: e.target.checked }); if (e.target.checked) setExpanded(topic.id); }} />
                  </label>

                  </div>
                </div>
                {open && <div className={`event-topic-details ${showMinimum ? "has-minimum" : ""}`}>
                  <div>
                {open && <div id={`topic-options-${topic.id}`} className="event-topic-options">
                  <p>{topic.multiple ? "Múltipla escolha" : "Escolha única"}</p>
                  <div className="chips">{topic.options.map((option) => <span className="chip" key={option}>{option}</span>)}</div>
                </div>}
                  </div>
                {showMinimum && <label className="event-topic-minimum">
                  Mínimo obrigatório
                  <input type="number" min={1} max={maximum} step={1} required value={rule.minimum} onChange={(e) => update(topic.id, { minimum: Math.max(1, Math.min(maximum, Number(e.target.value) || 1)) })} />
                  <small>{topic.multiple ? `O participante deve selecionar pelo menos ${rule.minimum} itens. Máximo permitido: ${maximum}.` : "Este tópico exige uma opção."}</small>
                </label>}
                </div>}


              </div>
            );
          })}
        </Accordion.Body>
      </Accordion.Item>
    </Accordion>
  );
}
