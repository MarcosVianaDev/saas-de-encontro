import { useEffect, useState, type FormEvent } from "react";
import { request } from "./backend-client";
import Form from "react-bootstrap/Form";
type Member = {
  id: string;
  email: string;
  name: string;
  role: string;
  permissions: string[];
  active: boolean;
  delegatedTo: string | null;
};
type Team = {
  canAssignAdministrator: boolean;
  permissions: string[];
  members: Member[];
};
const labels: Record<string, string> = {
  ADMIN: "Administrador do Evento",
  MODERATOR: "Moderador",
  OPERATOR: "Operador",
  reports: "Denúncias e moderação",
  blocks: "Análise de bloqueios",
  passes: "Operação de passes",
  activation: "Ativação de perfis",
  outfit: "Foto do look",
  remove_photo: "Remoção de fotos públicas",
  edit_bio: "Edição de descrição",
  location_exception: "Exceção de localização",
  announcements: "Avisos do evento",
};
export function TeamManagement({
  eventId,
  onChanged,
  readOnly = false,
}: {
  eventId: string;
  onChanged: () => void;
  readOnly?: boolean;
}) {
  const [data, setData] = useState<Team | null>(null),
    [editor, setEditor] = useState(false),
    [editingMemberId, setEditingMemberId] = useState<string | null>(null),
    [email, setEmail] = useState(""),
    [role, setRole] = useState("OPERATOR"),
    [permissions, setPermissions] = useState<string[]>([]),
    [active, setActive] = useState(true),
    [error, setError] = useState(""),
    [delegate, setDelegate] = useState<Member | null>(null);
  const load = () =>
    request<Team>("event-admin/team/")
      .then(setData)
      .catch((e) => setError(e.message));
  useEffect(() => {
    void load();
  }, [eventId]);
  function cancelEditor() {
    setEditor(false);
    setEditingMemberId(null);
    setEmail("");
    setRole("OPERATOR");
    setPermissions([]);
    setActive(true);
    setError("");
  }
  async function save(e: FormEvent) {
    e.preventDefault();
    try {
      await request("event-admin/team/", "POST", {
        email,
        role,
        permissions,
        active,
      });
      setEditor(false);
      void load();
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível salvar.");
    }
  }
  return (
    <>
      <div className="event-team-header">
        <h1>Equipe do evento</h1>
      {!readOnly && (
        <button
          className="adm-primary"
          onClick={() => {
            setEditor(true);
            setEditingMemberId(null);
            setEmail("");
            setRole("OPERATOR");
            setPermissions([]);
            setActive(true);
          }}
        >
          + Adicionar integrante
        </button>
      )}
      </div>
      <p>Papéis e vínculos administrativos</p>
      <section className="adm-card">
      <h2>Equipe e Permissões</h2>
      {error && <p role="alert">{error}</p>}
      {data?.members.filter((m) => !editor || !editingMemberId || m.id === editingMemberId).map((m) => (
        <article className="event-team-member" key={m.id}>
          <div className="event-team-member-details">
          <strong>{m.name}</strong>
          <p>
            {labels[m.role] || m.role} · {m.active ? "Ativo" : "Inativo"} ·{" "}
            {m.permissions.map((p) => labels[p] || p).join(", ") ||
              "Permissões do papel"}
          </p>
          {!readOnly && m.role === "MODERATOR" && m.active && (
            <button onClick={() => setDelegate(m)}>
              Transferir administração
            </button>
          )}
          </div>
          {!readOnly && (
            <button
              className="event-team-member-edit"
              onClick={() => {
                if (editor && editingMemberId === m.id) {
                  cancelEditor();
                  return;
                }
                setEditor(true);
                setEditingMemberId(m.id);
                setEmail(m.email);
                setRole(m.role);
                setPermissions(m.permissions);
                setActive(m.active);
              }}
            >
              {editor && editingMemberId === m.id ? "Cancelar" : "Editar"}
            </button>
          )}
        </article>
      ))}
      {!readOnly && editor && (
        <form onSubmit={save}>
          <label>
            Usuário (e-mail)
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label>
            Papel
            <select value={active ? role : "INACTIVE"} onChange={(e) => {
              const participates = e.target.value !== "INACTIVE";
              setActive(participates);
              if (participates) setRole(e.target.value);
            }}>
              <option value="INACTIVE">Não participa deste evento</option>
              {["ADMIN", "MODERATOR", "OPERATOR"]
                .filter(
                  (r) =>
                    r !== "ADMIN" ||
                    data?.canAssignAdministrator ||
                    role === "ADMIN",
                )
                .map((r) => (
                  <option key={r} value={r}>
                    {labels[r]}
                  </option>
                ))}
            </select>
          </label>
          <div className="event-team-permissions">
          {data?.permissions.map((p) => (
            <Form.Check
                key={p}
                id={`team-permission-${p}`}
                type="switch"
                label={labels[p] || p}
                checked={permissions.includes(p)}
                onChange={(e) =>
                  setPermissions(
                    e.target.checked
                      ? [...permissions, p]
                      : permissions.filter((x) => x !== p),
                  )
                }
              />
          ))}
          </div>
          <div className="event-team-form-actions">
            {!editingMemberId && (
              <button type="button" onClick={cancelEditor}>Cancelar</button>
            )}
            <button className="adm-primary" type="submit">Salvar</button>
          </div>
        </form>
      )}
      {delegate && (
        <section
          role="dialog"
          aria-modal="true"
          aria-label="Transferir administração"
        >
          <p>
            Transferir temporariamente a administração deste evento para{" "}
            {delegate.name}?
          </p>
          <p>
            Você continuará vinculado ao evento e poderá reassumir a
            administração posteriormente.
          </p>
          <button onClick={() => setDelegate(null)}>Cancelar</button>
          <button
            onClick={() =>
              void request("event-admin/team/", "POST", {
                action: "delegate",
                id: delegate.id,
                confirmed: true,
              })
                .then(() => {
                  setDelegate(null);
                  onChanged();
                })
                .catch((e) => setError(e.message))
            }
          >
            Transferir
          </button>
        </section>
      )}
    </section>
    </>
  );
}
