import { useState, type FormEvent } from "react";
import { api, request } from "./backend-client";
import type { Bootstrap, Profile } from "./types";

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
    [profile, setProfile] = useState<Profile>(data.profile),
    [photos, setPhotos] = useState(data.photos),
    [values, setValues] = useState<Record<string, Record<string, unknown>>>({}),
    [filters, setFilters] = useState(data.filters),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [locationReady, setLocationReady] = useState(
      data.event.mode === "ONLINE" || data.locationConsent,
    );
  const change = (key: keyof Profile, value: string) =>
    setProfile({ ...profile, [key]: value });
  async function next(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (step < 4) {
      setStep(step + 1);
      return;
    }
    setBusy(true);
    try {
      if (photos.length < 3) throw new Error("Adicione três fotos públicas.");
      if (data.event.mode !== "ONLINE" && !locationReady)
        throw new Error("Valide a localização antes de enviar para ativação.");
      await request("profile/fields/", "PUT", { values });
      await api.saveFilters(filters);
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
      <p>{step + 1} de 5</p>
      <progress max={5} value={step + 1} />
      <form onSubmit={next}>
        <h2>
          {
            [
              "Seu perfil",
              "Suas fotos",
              "Requisitos do evento",
              "Preferências",
              "Localização e revisão",
            ][step]
          }
        </h2>
        {step === 0 && (
          <>
            {[
              ["first", "Nome"],
              ["last", "Sobrenome"],
              ["month", "Mês de nascimento"],
              ["year", "Ano de nascimento"],
            ].map(([key, label]) => (
              <label key={key}>
                {label}
                <input
                  required
                  value={profile[key as keyof Profile]}
                  type={["month", "year"].includes(key) ? "number" : "text"}
                  min={key === "month" ? 1 : key === "year" ? 1900 : undefined}
                  max={key === "month" ? 12 : undefined}
                  onChange={(e) => change(key as keyof Profile, e.target.value)}
                />
              </label>
            ))}
            <label>
              Gênero
              <select
                value={profile.gender}
                onChange={(e) => change("gender", e.target.value)}
              >
                {[
                  "Mulheres",
                  "Homens",
                  "Não binário",
                  "Prefiro não informar",
                ].map((g) => (
                  <option key={g}>{g}</option>
                ))}
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
        {step === 2 && (
          <>
            {data.profileFields?.map((f) => (
              <label key={f.id}>
                {f.name}
                {f.required ? " (obrigatório)" : ""}
                {f.kind === "consent" ? (
                  <input
                    type="checkbox"
                    required={f.required}
                    checked={values[f.id]?.accepted === true}
                    onChange={(e) =>
                      setValues({
                        ...values,
                        [f.id]: {
                          accepted: e.target.checked,
                          version: f.version,
                        },
                      })
                    }
                  />
                ) : f.options.length ? (
                  <select
                    required={f.required}
                    value={String(values[f.id]?.answer || "")}
                    onChange={(e) =>
                      setValues({
                        ...values,
                        [f.id]: { answer: e.target.value },
                      })
                    }
                  >
                    <option value="">Selecione</option>
                    {f.options.map((o) => (
                      <option key={o}>{o}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    required={f.required}
                    value={String(values[f.id]?.answer || "")}
                    onChange={(e) =>
                      setValues({
                        ...values,
                        [f.id]: { answer: e.target.value },
                      })
                    }
                  />
                )}
              </label>
            ))}
            {!data.profileFields?.length && (
              <p>Não há requisitos adicionais.</p>
            )}
            <p>A equipe capturará sua foto do look e validará sua ativação.</p>
          </>
        )}
        {step === 3 && (
          <>
            <label>
              Idade mínima
              <input
                type="number"
                min={18}
                max={70}
                value={filters.min}
                onChange={(e) =>
                  setFilters({ ...filters, min: Number(e.target.value) })
                }
              />
            </label>
            <label>
              Idade máxima
              <input
                type="number"
                min={18}
                max={70}
                value={filters.max}
                onChange={(e) =>
                  setFilters({ ...filters, max: Number(e.target.value) })
                }
              />
            </label>
            <label>
              Gênero
              <select
                value={filters.gender}
                onChange={(e) =>
                  setFilters({ ...filters, gender: e.target.value })
                }
              >
                {["Todos", "Mulheres", "Homens"].map((g) => (
                  <option key={g}>{g}</option>
                ))}
              </select>
            </label>
            <p>Os filtros não serão flexibilizados automaticamente.</p>
          </>
        )}
        {step === 4 && (
          <>
            <p>
              {profile.first} {profile.last} · {photos.length} fotos
            </p>
            {data.event.mode !== "ONLINE" && (
              <>
                <p>
                  A localização é usada para validar sua presença no evento. Sua
                  posição exata não é exibida para outros participantes.
                </p>
                <button
                  type="button"
                  onClick={() => {
                    if (!navigator.geolocation) {
                      setError("Localização indisponível neste navegador.");
                      return;
                    }
                    navigator.geolocation.getCurrentPosition(
                      (p) =>
                        void request("location/", "POST", {
                          latitude: p.coords.latitude,
                          longitude: p.coords.longitude,
                          accuracy: p.coords.accuracy,
                        })
                          .then(() => setLocationReady(true))
                          .catch((e) => setError(e.message)),
                      () =>
                        setError(
                          "Permita a localização ou procure a equipe do evento.",
                        ),
                    );
                  }}
                >
                  Permitir localização
                </button>
                {locationReady && <p>Localização validada.</p>}
              </>
            )}
            <p>Seu perfil será enviado para ativação pela equipe.</p>
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
            {step === 4 ? "Enviar para ativação" : "Continuar"}
          </button>
        </div>
      </form>
    </main>
  );
}
