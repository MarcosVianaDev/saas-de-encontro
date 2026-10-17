import { useState, type FormEvent } from "react";
import { request } from "./backend-client";
import type { ProfileTopic } from "./types";

export function ProfileTopicManagement({ topics, onChanged }: { topics: ProfileTopic[]; onChanged: () => Promise<unknown> }) {
  const [draft, setDraft] = useState<{ id?: string; name: string; options: string; multiple: boolean; showInFilter: boolean; filterMultiple: boolean } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function save(e: FormEvent) {
    e.preventDefault();
    if (!draft) return;
    setBusy(true);
    setError("");
    try {
      await request("global/", "POST", { action: "save_topic", ...draft, options: draft.options.split(",").map((option) => option.trim()).filter(Boolean) });
      await onChanged();
      setDraft(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível salvar o tópico.");
    } finally { setBusy(false); }
  }
  return <div>
    <div className="client-team-header">
      <h3>Tópicos do perfil</h3>
      <button type="button" disabled={busy} onClick={() => { setError(""); setDraft({ name: "", options: "", multiple: false, showInFilter: false, filterMultiple: false }); }}>+ Novo tópico</button>
    </div>
    {error && <p role="alert">{error}</p>}
    {!draft && topics.map((topic) => <article key={topic.id}>
      <strong>{topic.name}</strong>
      <p>{topic.options.join(", ")}</p>
      <p>{topic.multiple ? "Múltipla escolha" : "Escolha única"}</p>
      <p>{topic.showInFilter ? "Exibido no filtro do participante" : "Oculto no filtro do participante"}</p>
      <button type="button" onClick={() => { setError(""); setDraft({ ...topic, showInFilter: topic.showInFilter === true, filterMultiple: topic.filterMultiple === true, options: topic.options.join(", ") }); }}>Editar</button>
    </article>)}
    {draft && <form onSubmit={save}>
      <fieldset disabled={busy}>
        <label>Nome do tópico<input required maxLength={200} value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} /></label>
        <label>Opções<textarea required value={draft.options} placeholder="Opções separadas por vírgula" onChange={(e) => setDraft({ ...draft, options: e.target.value })} /></label>
        <label>Permitir múltipla escolha<input type="checkbox" role="switch" className="app-toggle" checked={draft.multiple} onChange={(e) => setDraft({ ...draft, multiple: e.target.checked })} /></label>
        <label>Exibir no filtro<input type="checkbox" role="switch" className="app-toggle" checked={draft.showInFilter} onChange={(e) => setDraft({ ...draft, showInFilter: e.target.checked })} /></label>
        {draft.showInFilter && <div className="topic-filter-choice" role="group" aria-label="Tipo de escolha no filtro">
          <span className={!draft.filterMultiple ? "selected" : ""}>Escolha única</span>
          <label className="topic-filter-choice-control">
            <input type="checkbox" role="switch" className="app-toggle" aria-label="Escolha múltipla no filtro"
              checked={draft.filterMultiple} onChange={(event) => setDraft({ ...draft, filterMultiple: event.target.checked })} />
          </label>
          <span className={draft.filterMultiple ? "selected" : ""}>Escolha múltipla</span>
        </div>}
        <div className="event-team-form-actions">
          <button type="button" onClick={() => setDraft(null)}>Cancelar</button>
          <button type="submit" className="adm-primary">{busy ? "Salvando…" : "Salvar"}</button>
        </div>
      </fieldset>
    </form>}
  </div>;
}
