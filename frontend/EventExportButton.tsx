import { useEffect, useState } from "react";
import { request } from "./backend-client";

type Job = { id: string; state: string; progress: number; stage: string; error: string; download: string | null; term: string | null; expires: string | null; canRetry?: boolean };
export function EventExportButton({ eventId }: { eventId: string }) {
  const [job, setJob] = useState<Job | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let live = true;
    request<Job | null>("event-admin/exports/").then((value) => { if (live) setJob(value); }).catch((e) => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [eventId]);
  useEffect(() => {
    if (!job || !["PENDING", "PROCESSING"].includes(job.state)) return;
    let live = true;
    const timer = window.setInterval(() => {
      request<Job>(`event-admin/exports/${job.id}/`).then((value) => { if (live) { setJob(value); setError(""); } }).catch((e) => { if (live) setError(e.message); });
    }, 2000);
    return () => { live = false; window.clearInterval(timer); };
  }, [job?.id, job?.state]);
  const expired = Boolean(job?.expires && new Date(job.expires).getTime() <= Date.now());
  const running = Boolean(job && ["PENDING", "PROCESSING"].includes(job.state) && !job.canRetry);
  async function click() {
    if (job?.state === "COMPLETED" && !expired && job.download) { window.location.assign(job.download); return; }
    setBusy(true); setError("");
    try {
      setJob(await request<Job>(job?.canRetry || job?.state === "FAILED" || expired ? `event-admin/exports/${job!.id}/` : "event-admin/exports/", "POST", job?.canRetry || job?.state === "FAILED" || expired ? { action: "retry" } : {}));
    } catch (e) { setError(e instanceof Error ? e.message : "Não foi possível solicitar a exportação."); }
    finally { setBusy(false); }
  }
  return <div className="event-export-control">
    <button type="button" className="adm-primary" disabled={busy || running} onClick={() => void click()}>
      {busy ? "Solicitando exportação…" : running ? `${job?.stage} (${job?.progress}%)` : job?.state === "COMPLETED" && !expired ? "Baixar exportação ZIP" : job?.canRetry || job?.state === "FAILED" || expired ? "Tentar exportação novamente" : "Gerar exportação"}
    </button>
    <span role="status" aria-live="polite">{running ? job?.stage : job?.state === "COMPLETED" && !expired ? "Exportação concluída." : ""}</span>
    {job?.state === "COMPLETED" && !expired && job.term && <a className="client-password-button" href={job.term}>Baixar termo de integridade PDF</a>}
    {(error || job?.error) && <p role="alert">{error || job?.error}</p>}
  </div>;
}
