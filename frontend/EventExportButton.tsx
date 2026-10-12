import { useEffect, useState } from "react";
import Dropdown from "react-bootstrap/Dropdown";
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
    setBusy(true); setError("");
    try {
      setJob(await request<Job>(job?.canRetry || job?.state === "FAILED" || expired ? `event-admin/exports/${job!.id}/` : "event-admin/exports/", "POST", job?.canRetry || job?.state === "FAILED" || expired ? { action: "retry" } : {}));
    } catch (e) { setError(e instanceof Error ? e.message : "Não foi possível solicitar a exportação."); }
    finally { setBusy(false); }
  }
  return <div className="event-export-control">
    {job?.state === "COMPLETED" && !expired ? (
      <Dropdown>
        <Dropdown.Toggle className="adm-primary" id={`export-download-${job.id}`}>
          Baixar dados
        </Dropdown.Toggle>
        <Dropdown.Menu align="end">
          <Dropdown.Item href={job.term || undefined} disabled={!job.term}>Baixar o Termo</Dropdown.Item>
          <Dropdown.Item href={job.download || undefined} disabled={!job.download}>Baixar ZIP</Dropdown.Item>
        </Dropdown.Menu>
      </Dropdown>
    ) : (
    <button type="button" className="adm-primary" aria-live="polite" aria-busy={busy || running} disabled={busy || running} onClick={() => void click()}>
      {busy ? "Solicitando exportação…" : running ? `${job?.stage} (${job?.progress}%)` : "Exportar dados"}
    </button>
    )}
    {(error || job?.error) && <p role="alert">{error || job?.error}</p>}
  </div>;
}
