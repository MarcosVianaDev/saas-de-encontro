import { useState, type FormEvent } from "react";
import { request } from "./backend-client";

export function EventRequestForm({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: () => void;
}) {
  const [draft, setDraft] = useState<Record<string, string>>({
    mode: "PHYSICAL",
    radius_m: "100",
    tolerance_m: "1000",
    location_interval_minutes: "15",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const change = (key: string, value: string) =>
    setDraft((previous) => ({ ...previous, [key]: value }));
  const field = (
    key: string,
    label: string,
    type = "text",
    min?: number,
    max?: number,
  ) => (
    <label key={key}>
      {label}
      <input
        required
        type={type}
        value={draft[key] || ""}
        min={min}
        max={max}
        step={
          type === "number"
            ? ["latitude", "longitude"].includes(key)
              ? "any"
              : "1"
            : undefined
        }
        onChange={(e) => change(key, e.target.value)}
      />
    </label>
  );
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const body: Record<string, unknown> = {
        ...draft,
        starts: new Date(draft.starts).toISOString(),
        ends: new Date(draft.ends).toISOString(),
        auto_activate_participants: draft.auto_activate_participants === "true",
      };
      if (draft.mode === "ONLINE") {
        delete body.latitude;
        delete body.longitude;
      }
      await request("event-admin/requests/", "POST", body);
      onSaved();
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Não foi possível solicitar o evento.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="adm-card event-request-form">
      <h2>Solicitar novo evento</h2>
      <p>
        O evento será salvo como rascunho, na mesma organização, e dependerá de
        aprovação da Administração Global. Você será o responsável pelo evento.
      </p>
      <form onSubmit={save}>
        <fieldset disabled={busy} className="global-form-fields">
          {field("event", "Nome do evento")}
          <label>
            Descrição
            <textarea
              maxLength={4000}
              value={draft.description || ""}
              onChange={(e) => change("description", e.target.value)}
            />
          </label>
          <label>
            Modalidade
            <select
              aria-label="Modalidade"
              value={draft.mode}
              onChange={(e) => {
                change("mode", e.target.value);
                change("auto_activate_participants", "false");
              }}
            >
              <option value="ONLINE">Online</option>
              <option value="PHYSICAL">Presencial</option>
              <option value="HYBRID">Híbrido</option>
            </select>
          </label>
          {field("starts", "Início", "datetime-local")}
          {field("ends", "Término", "datetime-local")}
          {draft.mode !== "ONLINE" && (
            <>
              {field("latitude", "Latitude", "number", -90, 90)}
              {field("longitude", "Longitude", "number", -180, 180)}
              {field("radius_m", "Raio (metros)", "number", 1)}
              {field("tolerance_m", "Limite adicional (metros)", "number", 0)}
            </>
          )}
          {field(
            "location_interval_minutes",
            "Intervalo de localização (minutos)",
            "number",
            1,
          )}
          {draft.mode === "ONLINE" && (
            <>
              <p>
                O participante será considerado ausente após esse intervalo sem
                interação com o servidor. GPS não é solicitado.
              </p>
              <label>
                <input
                  type="checkbox"
                  role="switch"
                  className="app-toggle"
                  checked={draft.auto_activate_participants === "true"}
                  onChange={(e) =>
                    change(
                      "auto_activate_participants",
                      String(e.target.checked),
                    )
                  }
                />
                Ativar automaticamente ao completar o perfil
              </label>
              <p>
                Exige três fotos públicas, uma principal, bio e campos
                obrigatórios e termos. Dispensa foto de outfit e aprovação da
                organização.
              </p>
            </>
          )}
          {error && <p role="alert">{error}</p>}
          <div className="adm-actions">
            <button type="button" onClick={onClose}>
              Cancelar
            </button>
            <button className="adm-primary" type="submit">
              {busy ? "Salvando…" : "Salvar solicitação"}
            </button>
          </div>
        </fieldset>
      </form>
    </section>
  );
}
