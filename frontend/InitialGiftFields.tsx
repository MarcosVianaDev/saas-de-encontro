export function initialGiftPayload(draft: Record<string, string>) {
  return draft.initial_gift === "true" ? {
    enabled: true,
    name: draft.gift_name || "",
    delay_minutes: Number(draft.gift_delay || 0),
    duration_minutes: draft.gift_type === "duration" ? Number(draft.gift_amount || 0) : 0,
    reveal_limit: draft.gift_type === "duration" ? 0 : Number(draft.gift_amount || 0),
  } : { enabled: false };
}

export function InitialGiftFields({ draft, onChange }: {
  draft: Record<string, string>;
  onChange: (key: string, value: string) => void;
}) {
  const durationMinutes = (new Date(draft.ends).getTime() - new Date(draft.starts).getTime()) / 60000;
  const maximumDelay = Number.isFinite(durationMinutes) && durationMinutes > 0 ? Math.min(525600, Math.max(0, Math.ceil(durationMinutes) - 1)) : 525600;
  return <section className="initial-gift-fields">
    <label>
      Presente inicial
      <input type="checkbox" role="switch" className="app-toggle" checked={draft.initial_gift === "true"} onChange={(e) => onChange("initial_gift", String(e.target.checked))} />
    </label>
    {draft.initial_gift === "true" && <>
      <label>Nome do passe<input required maxLength={200} value={draft.gift_name || ""} onChange={(e) => onChange("gift_name", e.target.value)} /></label>
      <div className="event-form-pair">
        <label>Tipo de passe
          <select value={draft.gift_type || "quantity"} onChange={(e) => onChange("gift_type", e.target.value)}>
            <option value="quantity">Quantidade de revelações</option>
            <option value="duration">Duração em minutos</option>
          </select>
        </label>
        <label>{draft.gift_type === "duration" ? "Duração do passe (minutos)" : "Quantidade de revelações"}
          <input type="number" required min={1} max={draft.gift_type === "duration" ? 525600 : 1000000} step={1} value={draft.gift_amount || ""} onChange={(e) => onChange("gift_amount", e.target.value)} />
        </label>
      </div>
      <label>Presentear após quantos minutos de evento?
        <input type="number" required min={0} max={maximumDelay} step={1} value={draft.gift_delay || "0"} onChange={(e) => onChange("gift_delay", e.target.value)} />
      </label>
      <p>Com 0 minutos, o participante recebe o passe já ativado ao ativar seu perfil. Com um prazo maior, a entrega ocorre após esse tempo a partir do início do evento, para participantes com perfil ativo.</p>
      <p>O presente é gratuito, vale para qualquer modalidade e será informado por uma notificação.</p>
      {Number.isFinite(durationMinutes) && durationMinutes > 0 && <p>O presente deve ser entregue antes do término do evento. Prazo máximo: {maximumDelay} minutos.</p>}
    </>}
  </section>;
}
