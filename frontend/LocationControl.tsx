import { useEffect, useRef, useState } from "react";
import { request } from "./backend-client";
import type { Bootstrap } from "./types";

export function LocationControl({
  data,
  onChanged,
  onSupport,
}: {
  data: Bootstrap;
  onChanged: (d: Bootstrap) => void;
  onSupport: () => void;
}) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const callback = useRef(onChanged);
  callback.current = onChanged;
  const reading = (phase = "manual") => {
    if (!navigator.geolocation) {
      setError("Este navegador não oferece localização. Procure a equipe.");
      return;
    }
    setBusy(true);
    navigator.geolocation.getCurrentPosition(
      (p) => {
        void request<Bootstrap>("location/", "POST", {
          latitude: p.coords.latitude,
          longitude: p.coords.longitude,
          accuracy: p.coords.accuracy,
        })
          .then((d) => {
            callback.current(d);
            setError("");
          })
          .catch((e) => setError(e.message))
          .finally(() => setBusy(false));
      },
      (e) => {
        if (e.code === 1)
          void request<Bootstrap>("location/", "POST", { action: "deny" })
            .then(callback.current)
            .catch((err) => setError(err.message));
        else
          void request<Bootstrap>("location/", "POST", {
            action: "failed",
            phase,
          })
            .then(callback.current)
            .catch((err) => setError(err.message));
        setError(
          "Não foi possível confirmar sua localização. Verifique sua conexão e as permissões de localização.",
        );
        setBusy(false);
      },
      { enableHighAccuracy: false, timeout: 20000, maximumAge: 0 },
    );
  };
  useEffect(() => {
    if (
      data.event.mode === "ONLINE" ||
      data.event.readOnly ||
      !data.locationConsent
    )
      return;
    const t = setInterval(
      () => reading("periodic"),
      (data.event.locationInterval || 15) * 60000,
    );
    return () => clearInterval(t);
  }, [
    data.event.id,
    data.event.mode,
    data.event.readOnly,
    data.locationConsent,
    data.event.locationInterval,
  ]);
  useEffect(() => {
    if (
      !data.location?.failed ||
      data.location.exhausted ||
      data.event.readOnly
    )
      return;
    const t = setTimeout(() => reading("retry"), 60000);
    return () => clearTimeout(t);
  }, [
    data.location?.failed,
    data.location?.retries,
    data.location?.exhausted,
    data.event.readOnly,
  ]);
  if (data.event.mode === "ONLINE" || data.event.readOnly) return null;
  return (
    <section className="participant-tools">
      <h3>
        {data.location?.technicalInactive
          ? "Não conseguimos validar sua localização"
          : "Presença no evento"}
      </h3>
      {!data.locationConsent && (
        <p>
          A localização é usada para validar sua presença no evento e aplicar
          regras de segurança. Sua posição exata não é exibida para outros
          participantes.
        </p>
      )}
      {data.location?.technicalInactive && (
        <p>
          Seu perfil foi temporariamente desativado. Você pode tentar novamente
          ou procurar a equipe do evento.
        </p>
      )}
      {data.locationConsent && !data.location?.failed && (
        <p>
          {data.presence === "PRESENT"
            ? "Presença confirmada"
            : data.presence === "OUTSIDE"
              ? "Temporariamente fora"
              : "Presença ainda não confirmada"}
        </p>
      )}
      {data.location?.failed && (
        <p>
          Não foi possível confirmar sua localização. Verifique sua conexão e as
          permissões de localização. {data.location.retries} de 5 retentativas.
        </p>
      )}
      {data.location?.exceptionUntil && (
        <p>
          Exceção temporária até{" "}
          {new Date(data.location.exceptionUntil).toLocaleString("pt-BR")}.
        </p>
      )}
      <button disabled={busy} onClick={() => reading()}>
        {data.location?.technicalInactive
          ? "Tentar novamente"
          : data.locationConsent
            ? "Verificar agora"
            : "Permitir localização"}
      </button>
      {data.location?.technicalInactive && (
        <button onClick={onSupport}>Falar com a equipe</button>
      )}
      {!data.locationConsent && (
        <button
          onClick={() =>
            void request<Bootstrap>("location/", "POST", {
              action: "deny",
            }).then(callback.current)
          }
        >
          Agora não
        </button>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
