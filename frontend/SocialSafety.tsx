import { CachedImage } from "./CachedImage";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { request } from "./backend-client";
import type { Bootstrap, Person } from "./types";
import { closeDialogOnBackdrop } from "./modal-backdrop";

export function SocialSafety({
  person,
  onChanged,
  allowBlock = false,
}: {
  person: Person;
  onChanged: (d: Bootstrap) => void;
  allowBlock?: boolean;
}) {
  const [photos, setPhotos] = useState<{ id: string; url: string }[]>([]),
    [messages, setMessages] = useState<{ id: string; body: string }[]>([]),
    [photo, setPhoto] = useState(""),
    [message, setMessage] = useState(""),
    [success, setSuccess] = useState("");
  const [mode, setMode] = useState(""),
    [reasons, setReasons] = useState<string[]>([]),
    [selected, setSelected] = useState<string[]>([]),
    [body, setBody] = useState(""),
    [context, setContext] = useState(""),
    [photoChanged, setPhotoChanged] = useState(false),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (mode) {
      dialog.current?.showModal();
      setError("");
      if (mode === "report")
        void request<{
          reasons: string[];
          photos: { id: string; url: string }[];
          messages: { id: string; body: string }[];
        }>(`reports/${person.id}/`)
          .then((d) => {
            setReasons(d.reasons);
            setPhotos(d.photos);
            setMessages(d.messages);
          })
          .catch((e) => setError(e.message));
    } else dialog.current?.close();
  }, [mode, person.id]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "block") {
        onChanged(
          await request<Bootstrap>(`blocks/${person.id}/`, "POST", {
            confirmed: true,
            reason: body,
          }),
        );
      } else {
        await request(`reports/${person.id}/`, "POST", {
          description: body,
          reasons: selected,
          evidence: {
            context,
            photoChanged,
            photo: photo || undefined,
            message: message || undefined,
          },
        });
      }
      setSuccess(
        mode === "block"
          ? "Participante bloqueado neste evento."
          : "Denúncia enviada. A equipe do evento poderá analisar a ocorrência.",
      );
      setMode("");
      setBody("");
      setSelected([]);
      setPhoto("");
      setMessage("");
      setContext("");
      setPhotoChanged(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível enviar.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="safety-controls">
        {allowBlock && (
          <button onClick={() => setMode("block")}>Bloquear</button>
        )}
        <button onClick={() => setMode("report")}>Denunciar</button>
      </div>
      <dialog
        ref={dialog}
        onCancel={() => setMode("")}
        onClick={(e) => closeDialogOnBackdrop(e, () => setMode(""))}
      >
        <form onSubmit={submit}>
          <h2>
            {mode === "block"
              ? `Bloquear ${person.name}?`
              : "Denunciar participante"}
          </h2>
          {mode === "block" ? (
            <p>
              Vocês deixarão de aparecer um para o outro neste evento. O
              bloqueio não poderá ser desfeito pelo participante.
            </p>
          ) : (
            <>
              {reasons.map((r) => (
                <label key={r}>
                  <input
                    type="checkbox"
                    checked={selected.includes(r)}
                    onChange={(e) =>
                      setSelected(
                        e.target.checked
                          ? [...selected, r]
                          : selected.filter((x) => x !== r),
                      )
                    }
                  />
                  {r}
                </label>
              ))}
              <label>
                Adicionar evidência: foto, mensagem ou outro contexto
                <textarea
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                />
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={photoChanged}
                  onChange={(e) => setPhotoChanged(e.target.checked)}
                />
                A foto relacionada já foi alterada ou removida
              </label>
              {photoChanged && (
                <p>
                  Procure também a moderação do evento. O histórico poderá ser
                  analisado pela equipe autorizada.
                </p>
              )}
            </>
          )}
          {mode === "report" && (
            <>
              <label>
                Foto relacionada
                <select
                  value={photo}
                  onChange={(e) => setPhoto(e.target.value)}
                >
                  <option value="">Sem foto</option>
                  {photos.map((p, i) => (
                    <option key={p.id} value={p.id}>
                      Foto {i + 1}
                    </option>
                  ))}
                </select>
              </label>
              {photo && (
                <CachedImage
                  src={photos.find((p) => p.id === photo)?.url}
                  alt="Foto selecionada como evidência"
                  style={{ maxWidth: 160 }}
                />
              )}
              <label>
                Mensagem relacionada
                <select
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                >
                  <option value="">Sem mensagem</option>
                  {messages.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.body.slice(0, 100)}
                    </option>
                  ))}
                </select>
              </label>
            </>
          )}
          <label>
            {mode === "block" ? "Motivo" : "Conte o que aconteceu"}
            <textarea
              required={mode === "report"}
              maxLength={4000}
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
          </label>
          {error && <p role="alert">{error}</p>}
          <div className="onboarding-actions">
            <button type="button" onClick={() => setMode("")}>
              Cancelar
            </button>
            <button disabled={busy}>
              {mode === "block" ? "Bloquear" : "Enviar denúncia"}
            </button>
          </div>
        </form>
      </dialog>
      {success && <p role="status">{success}</p>}
    </>
  );
}
