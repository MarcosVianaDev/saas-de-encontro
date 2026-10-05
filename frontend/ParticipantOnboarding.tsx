import { useState, type FormEvent } from "react";
import { api, request } from "./backend-client";
import type { Bootstrap, Profile } from "./types";
import { birthMonths, birthYears, latestBirthYear } from "./birth-options";

export function ParticipantOnboarding({
  data,
  onComplete,
  onLogout,
}: {
  data: Bootstrap;
  onComplete: (d: Bootstrap) => void;
  onLogout: () => void;
}) {
  const [step, setStep] = useState(0),
    [profile, setProfile] = useState<Profile>({
      ...data.profile,
      year: data.profile.year || String(latestBirthYear),
    }),
    [photos, setPhotos] = useState(data.photos),
    [values, setValues] = useState<Record<string, Record<string, unknown>>>({}),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const fields = data.profileFields || [];
  const steps = fields.length
    ? ["Seu perfil", "Suas fotos", "Requisitos do evento"]
    : ["Seu perfil", "Suas fotos"];
  const change = (key: keyof Profile, value: string) =>
    setProfile({ ...profile, [key]: value });
  async function next(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (step < steps.length - 1) {
      setStep(step + 1);
      return;
    }
    setBusy(true);
    try {
      if (photos.length < 3) throw new Error("Adicione três fotos públicas.");
      if (fields.length) await request("profile/fields/", "PUT", { values });
      onComplete(await api.saveProfile(profile));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível concluir.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="participant-onboarding">
      <h1>{data.event.name}</h1>
      <p>
        {step + 1} de {steps.length}
      </p>
      <progress max={steps.length} value={step + 1} />
      <form onSubmit={next}>
        <h2>{steps[step]}</h2>
        {step === 0 && (
          <>
            {[
              ["first", "Nome"],
              ["last", "Sobrenome"],
            ].map(([key, label]) => (
              <label key={key}>
                {label}
                <input
                  required
                  value={profile[key as keyof Profile]}
                  type="text"
                  onChange={(e) => change(key as keyof Profile, e.target.value)}
                />
              </label>
            ))}
            <label>
              Mês de nascimento
              <select
                required
                value={profile.month}
                onChange={(e) => change("month", e.target.value)}
              >
                {birthMonths.map((month, index) => (
                  <option key={month} value={index + 1}>
                    {month}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Ano de nascimento
              <select
                required
                value={profile.year}
                onChange={(e) => change("year", e.target.value)}
              >
                {birthYears.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Gênero
              <select
                value={profile.gender}
                onChange={(e) => change("gender", e.target.value)}
              >
                <option value="Homens">Masculino</option>
                <option value="Mulheres">Feminino</option>
                <option value="Não binário">Não binário</option>
                <option value="Prefiro não informar">
                  Prefiro não informar
                </option>
              </select>
            </label>
            <label>
              Sobre você
              <textarea
                required
                minLength={50}
                maxLength={200}
                value={profile.bio}
                onChange={(e) => change("bio", e.target.value)}
              />
            </label>
          </>
        )}
        {step === 1 && (
          <>
            <p>
              Adicione 3 fotos públicas para ativar seu perfil. Após a
              aprovação, essas fotos não podem ser alteradas diretamente.
            </p>
            <div className="onboarding-photos">
              {[0, 1, 2].map((i) => (
                <article key={i}>
                  <strong>Foto pública {i + 1}</strong>
                  {photos[i] && (
                    <>
                      <img src={photos[i]} alt={`Foto pública ${i + 1}`} />
                      <button
                        type="button"
                        onClick={() =>
                          void api
                            .removePhoto(photos[i])
                            .then((d) => setPhotos(d.photos))
                            .catch((e) => setError(e.message))
                        }
                      >
                        Trocar foto
                      </button>
                    </>
                  )}
                </article>
              ))}
            </div>
            <label>
              Adicionar fotos
              <input
                type="file"
                multiple
                accept="image/jpeg,image/png,image/webp"
                disabled={busy}
                onChange={async (e) => {
                  setBusy(true);
                  try {
                    for (const file of Array.from(e.target.files || [])) {
                      const result = await api.upload(file);
                      setPhotos(result.photos);
                    }
                  } catch (e) {
                    setError(
                      e instanceof Error ? e.message : "Falha no envio.",
                    );
                  } finally {
                    setBusy(false);
                  }
                }}
              />
            </label>
          </>
        )}
        {step === 2 && fields.length > 0 && (
          <>
            {fields.map((field) => (
              <label key={field.id}>
                {field.name}
                {field.required ? " (obrigatório)" : ""}
                {field.kind === "consent" ? (
                  <input
                    type="checkbox"
                    required={field.required}
                    checked={values[field.id]?.accepted === true}
                    onChange={(e) =>
                      setValues({
                        ...values,
                        [field.id]: {
                          accepted: e.target.checked,
                          version: field.version,
                        },
                      })
                    }
                  />
                ) : field.options.length ? (
                  <select
                    required={field.required}
                    value={String(values[field.id]?.answer || "")}
                    onChange={(e) =>
                      setValues({
                        ...values,
                        [field.id]: { answer: e.target.value },
                      })
                    }
                  >
                    <option value="">Selecione</option>
                    {field.options.map((option) => (
                      <option key={option}>{option}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    required={field.required}
                    value={String(values[field.id]?.answer || "")}
                    onChange={(e) =>
                      setValues({
                        ...values,
                        [field.id]: { answer: e.target.value },
                      })
                    }
                  />
                )}
              </label>
            ))}
          </>
        )}
        {error && <p role="alert">{error}</p>}
        <div className="onboarding-actions">
          <button
            type="button"
            onClick={() => (step ? setStep(step - 1) : onLogout())}
          >
            {step ? "Voltar" : "Sair da conta"}
          </button>
          <button className="primary" disabled={busy}>
            {step === steps.length - 1 ? "Enviar para ativação" : "Continuar"}
          </button>
        </div>
      </form>
    </main>
  );
}
