import { useEffect, useState, type FormEvent } from "react";
import { request } from "./backend-client";

type Config = { state: string; configuration: Record<string, unknown> };
export function EventConfiguration({
  eventId,
  canEditDates = false,
}: {
  eventId: string;
  canEditDates?: boolean;
}) {
  const [data, setData] = useState<Config | null>(null);
  const [draft, setDraft] = useState<Record<string, unknown>>({});
  const [dirty, setDirty] = useState(false);
  const [confirmation, setConfirmation] = useState(false);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    void request<Config>("event-admin/configuration/")
      .then((d) => {
        setData(d);
        setDraft(d.configuration);
      })
      .catch((e) => setMessage(e.message));
  }, [eventId]);
  const frozen = data && !["DRAFT", "SCHEDULED"].includes(data.state);
  const started =
    data && ["RUNNING", "PAUSED", "CLOSED", "ARCHIVED"].includes(data.state);
  const fields = (items: [string, string, string][], location = false) =>
    items.map(([key, label, type]) => (
      <label key={key}>
        {label}
        <input
          disabled={Boolean(
            (location ? started : frozen) ||
            (type === "datetime-local" && !canEditDates),
          )}
          type={type}
          step={type === "number" ? "any" : undefined}
          value={
            draft[key] == null
              ? ""
              : type === "datetime-local"
                ? String(draft[key]).length === 16
                  ? String(draft[key])
                  : new Date(
                      new Date(String(draft[key])).getTime() -
                        new Date().getTimezoneOffset() * 60000,
                    )
                      .toISOString()
                      .slice(0, 16)
                : String(draft[key])
          }
          onChange={(e) => {
            setDirty(true);
            setDraft({
              ...draft,
              [key]:
                type === "number"
                  ? e.target.value === ""
                    ? null
                    : Number(e.target.value)
                  : e.target.value,
            });
          }}
        />
      </label>
    ));
  async function save(e: FormEvent) {
    e.preventDefault();
    if (data?.state === "SCHEDULED" && !confirmation) {
      setConfirmation(true);
      return;
    }
    setBusy(true);
    try {
      const body = Object.fromEntries(
        Object.entries(draft).filter(
          ([key, value]) => value !== data?.configuration[key],
        ),
      );
      for (const key of ["starts_at", "ends_at"])
        if (body[key]) body[key] = new Date(String(body[key])).toISOString();
      const d = await request<Config>("event-admin/configuration/", "PUT", {
        ...body,
        confirmed: confirmation,
      });
      setData(d);
      setDraft(d.configuration);
      setDirty(false);
      setConfirmation(false);
      setMessage("Configurações atualizadas.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Não foi possível salvar.");
    } finally {
      setBusy(false);
    }
  }
  if (!data)
    return (
      <section className="adm-card">
        <h2>Configurações</h2>
        <p role="status">{message || "Carregando configurações…"}</p>
      </section>
    );
  return (
    <form className="adm-card" onSubmit={save}>
      <h2>Configurações</h2>
      <h3>Informações gerais</h3>
      {fields([
        ["name", "Nome", "text"],
        ["description", "Descrição", "text"],
      ])}
      <label>
        Modalidade
        <select
          disabled={Boolean(frozen)}
          value={String(draft.mode || "ONLINE")}
          onChange={(e) => {
            setDirty(true);
            setDraft({ ...draft, mode: e.target.value, settings: { ...(draft.settings as Record<string, unknown> || {}), auto_activate_participants: false } });
          }}
        >
          <option value="ONLINE">Online</option>
          <option value="PHYSICAL">Presencial</option>
          <option value="HYBRID">Híbrido</option>
        </select>
      </label>
      <h3>Datas e horários</h3>
      {fields([
        ["starts_at", "Início", "datetime-local"],
        ["ends_at", "Término", "datetime-local"],
      ])}
      <h3>Localização</h3>
      {draft.mode !== "ONLINE" && fields(
        [
          ["latitude", "Latitude", "number"],
          ["longitude", "Longitude", "number"],
          ["radius_m", "Raio (metros)", "number"],
          ["tolerance_m", "Limite adicional (metros)", "number"],
        ],
        true,
      )}
      {fields([
        [
          "location_interval_minutes",
          "Intervalo de localização (minutos)",
          "number",
        ],
      ])}
      {draft.mode === "ONLINE" && <p>O participante será considerado ausente após esse intervalo sem interação com o servidor. GPS não é solicitado.</p>}
      <h3>Participantes e ativação</h3>
      <p>Os campos obrigatórios são configurados antes da abertura.</p>
      {draft.mode === "ONLINE" && (
        <label>
          <input type="checkbox" disabled={Boolean(frozen)}
            checked={(draft.settings as Record<string, unknown>)?.auto_activate_participants === true}
            onChange={(e) => { setDirty(true); setDraft({ ...draft, settings: { ...(draft.settings as Record<string, unknown> || {}), auto_activate_participants: e.target.checked } }); }} />
          Ativar automaticamente ao completar o perfil
          <p>Exige três fotos públicas, uma principal, bio e todos os campos obrigatórios e termos. Dispensa foto de outfit e aprovação da organização.</p>
        </label>
      )}
      <h3>Passes</h3>
      <label>
        Instruções de pagamento e ativação
        <textarea
          disabled={Boolean(started) || !canEditDates}
          maxLength={4000}
          value={String(draft.pass_payment_instructions || "")}
          onChange={(e) => {
            setDirty(true);
            setDraft({ ...draft, pass_payment_instructions: e.target.value });
          }}
        />
      </label>
      <p>
        A gestão global define estas instruções até o início do evento. A
        concessão é registrada manualmente pela equipe autorizada.
      </p>
      <p>As ofertas são gerenciadas na operação de passes do evento.</p>
      <h3>Notificações</h3>
      <p>
        Os avisos podem ser criados e agendados na área de Avisos do Evento.
      </p>
      <h3>Privacidade e retenção</h3>
      <p>
        Os prazos por categoria dependem da política aprovada. O arquivamento
        não elimina dados.
      </p>
      {frozen && (
        <p>
          Esta configuração não pode mais ser alterada porque o evento já está
          aberto ou em andamento.
        </p>
      )}
      {confirmation && (
        <p role="alert">
          O evento já foi agendado. Alterar esta configuração pode afetar
          participantes já cadastrados.
        </p>
      )}
      {dirty && (
        <div className="adm-actions configuration-actions">
          <button
            type="button"
            onClick={() => {
              setDraft(data?.configuration || {});
              setDirty(false);
              setConfirmation(false);
            }}
          >
            Voltar
          </button>
          <button className="adm-primary" disabled={busy} type="submit">
            {confirmation ? "Confirmar alteração" : "Salvar alterações"}
          </button>
        </div>
      )}
      {message && <p role="status">{message}</p>}
    </form>
  );
}
