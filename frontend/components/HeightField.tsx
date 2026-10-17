export function HeightField({ value, onChange }: {
  value?: number | null;
  onChange: (height: number | null) => void;
}) {
  return (
    <label className="field">
      <span>Altura em centímetros (opcional)</span>
      <input type="number" inputMode="numeric" min={50} max={250} step={1}
        placeholder="Ex.: 170" value={value ?? ""}
        onChange={(event) => onChange(event.target.value === "" ? null : Number(event.target.value))} />
    </label>
  );
}
