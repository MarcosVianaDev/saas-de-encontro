import type { AdminData, Case, Participant } from "./Administration";

let sequence = 0;
const mockId = () => `demo-action-${Date.now()}-${++sequence}`;
const time = (minutes = 0) =>
  new Date(Date.now() + minutes * 60000).toISOString();
const image = (file: string) => `/images/${file}.jpg`;
const profiles = [
  [
    "Camila Souza",
    28,
    "Designer de Produto",
    "photo-1544005313-94ddf0286df2",
    "Ativo",
  ],
  [
    "Lucas Oliveira",
    32,
    "Desenvolvedor",
    "photo-1500648767791-00dcc994a43e",
    "Ativo",
  ],
  [
    "Mariana Lima",
    26,
    "Marketing",
    "photo-1524504388940-b1c1722653e1",
    "Ativo",
  ],
  [
    "Rafael Costa",
    30,
    "Empresário",
    "photo-1519085360753-af0119f7cbe7",
    "Ativo",
  ],
  [
    "Aline Martins",
    27,
    "Consultora",
    "photo-1534528741775-53994a69daeb",
    "Banido",
  ],
  [
    "Thiago Almeida",
    29,
    "Analista de Dados",
    "photo-1506794778202-cad84cf45f1d",
    "Ativo",
  ],
  [
    "João Pedro",
    31,
    "Desenvolvedor",
    "photo-1535713875002-d1d0cf377fde",
    "Ativo",
  ],
  [
    "Ana Carolina",
    26,
    "Marketing",
    "photo-1531123897727-8f129e1688ce",
    "Ativo",
  ],
  [
    "Bruno Santos",
    28,
    "Analista",
    "photo-1463453091185-61582044d556",
    "Cadastro incompleto",
  ],
  [
    "Beatriz Lima",
    31,
    "Jornalista",
    "photo-1524250502761-1ac6f2e30d43",
    "Ativo",
  ],
  [
    "Carlos Menezes",
    29,
    "Arquiteto",
    "photo-1507591064344-4c6ce005b128",
    "Suspenso",
  ],
  [
    "Júlia Ferreira",
    28,
    "Advogada",
    "photo-1526510747491-58f928ec870f",
    "Ativo",
  ],
] as const;

function fixture(id: string, status: string, name: string): AdminData {
  const participants: Participant[] = profiles.map(
    ([name, age, job, file, situation], i) => ({
      id: `${id}-person-${i + 1}`,
      name,
      age,
      job,
      email: `pessoa${i + 1}@example.test`,
      image: image(file),
      status: situation,
      reason:
        situation === "Suspenso"
          ? "Exemplo fictício: restrição temporária para análise."
          : situation === "Banido"
            ? "Exemplo fictício de decisão administrativa no evento."
            : "",
      created: time(-i * 42 - 8),
      updated: time(-i * 7),
      lastSeen:
        i === 8 ? null : time([0, 2, 5, 7, 11].includes(i) ? -(i % 5) : -i * 7),
      online: [0, 2, 5, 7, 11].includes(i),
      reports: 0,
      blocks: 0,
    }),
  );
  const makeCase = (
    index: number,
    peer: number,
    reporter: number,
    reason: string,
    state: string,
  ): Case => ({
    id: `${id}-case-${index}`,
    reference: `DEMO-${String(index).padStart(5, "0")}`,
    reported: participants[peer],
    reporter: participants[reporter],
    author: participants[reporter].email,
    kind: "Denúncia",
    priority: index === 1 ? 2 : 1,
    reason,
    description:
      "Relato inteiramente fictício para demonstrar a análise de uma ocorrência. Não se refere a pessoas ou acontecimentos reais.",
    status: state,
    created: time(-index * 24),
    closed: state === "Resolvida" ? time(-12) : null,
    responsible: state === "Pendente" ? null : "Ana Carolina · Moderadora",
    notes:
      state === "Pendente"
        ? []
        : [
            {
              id: `${id}-note-${index}`,
              author: "Ana Carolina · Moderadora",
              body: "Exemplo de nota interna: contexto registrado para acompanhamento.",
              created: time(-15),
            },
          ],
    history: [
      {
        id: `${id}-history-${index}`,
        author: "Sistema de demonstração",
        body: "Ocorrência criada. Administração do evento e plataforma notificadas na simulação.",
        created: time(-index * 24),
      },
      ...(state !== "Pendente"
        ? [
            {
              id: `${id}-assumed-${index}`,
              author: "Ana Carolina · Moderadora",
              body: "Ocorrência assumida para análise.",
              created: time(-18),
            },
          ]
        : []),
      ...(state === "Resolvida"
        ? [
            {
              id: `${id}-resolved-${index}`,
              author: "Marcos Viana · Administrador",
              body: "Ocorrência resolvida: exemplo de conclusão sem sanção adicional.",
              created: time(-12),
            },
          ]
        : []),
    ],
    evidence:
      index === 1
        ? [
            {
              id: `${id}-evidence-1`,
              description: "Imagem ilustrativa do evento; evidência fictícia.",
              content: image("photo-1470229722913-7c0e2dbbafd3"),
            },
            {
              id: `${id}-evidence-2`,
              description:
                "Registro textual fictício de atendimento para análise.",
              content: null,
            },
          ]
        : [],
  });
  const cases = [
    makeCase(1, 6, 7, "Assédio ou comportamento inadequado", "Pendente"),
    makeCase(2, 1, 2, "Conteúdo impróprio", "Pendente"),
    makeCase(3, 3, 0, "Comportamento agressivo", "Em análise"),
    makeCase(4, 10, 9, "Spam", "Resolvida"),
  ];
  cases[3].kind = "Administrativa";
  cases[3].reporter = null;
  cases[3].author = "Marcos Viana · Administrador";
  participants.forEach((p) => {
    p.reports = cases.filter((c) => c.reported.id === p.id).length;
  });
  participants[3].blocks = 5;
  participants[6].blocks = 3;
  if (status === "Agendado") {
    participants.splice(4);
    cases.splice(0);
    participants.forEach((p) => {
      p.status = "Cadastro incompleto";
      p.online = false;
      p.reports = 0;
      p.blocks = 0;
    });
  }
  if (status === "Encerrado") {
    participants.forEach((p) => {
      p.online = false;
    });
    cases.forEach((c) => {
      c.status = "Resolvida";
      c.closed = time(-1440);
    });
  }
  return {
    role: "ADMIN",
    events: [],
    event: {
      id,
      name,
      description:
        "Networking, novas conexões e uma experiência fictícia completa.",
      starts: time(
        status === "Agendado" ? 2880 : status === "Encerrado" ? -4320 : -180,
      ),
      ends: time(
        status === "Encerrado" ? -2880 : status === "Agendado" ? 3180 : 180,
      ),
      status,
      joinPath: status === "Encerrado" ? null : `/?demoEvent=${id}#login`,
      responsible: ["Marcos Viana"],
    },
    participants,
    cases,
    blockSignals: participants
      .filter((p) => (p.blocks || 0) > 0)
      .map((p) => ({
        participant: p,
        timeline: Array.from({ length: p.blocks || 0 }, (_, i) =>
          time(-120 + i * 18),
        ),
      })),
    metrics: {
      participants: participants.length,
      active: participants.filter((p) => p.status === "Ativo" && p.online)
        .length,
      new: participants.filter(
        (p) => new Date(p.created).getTime() >= Date.now() - 3600000,
      ).length,
      matches: status === "Agendado" ? 0 : 8,
      conversations: status === "Agendado" ? 0 : 6,
      blocks: participants.reduce((sum, p) => sum + (p.blocks || 0), 0),
    },
    team: [
      { id: "team-admin", name: "Marcos Viana", role: "Administrador" },
      { id: "team-mod", name: "Ana Carolina", role: "Moderador" },
      { id: "team-operator", name: "Carlos Silva", role: "Operador" },
      { id: "team-support", name: "Juliana Costa", role: "Operador" },
    ],
  };
}
let events: AdminData[];
let selected = "demo-current";
let role = "ADMIN";
function reset() {
  events = [
    fixture("demo-current", "Em andamento", "Evento Conexões 2026"),
    fixture("demo-scheduled", "Agendado", "Próximo Encontro"),
    fixture("demo-ended", "Encerrado", "Encontro de Primavera"),
  ];
  selected = "demo-current";
  role = "ADMIN";
}
reset();
function snapshot(): AdminData {
  const data = structuredClone(events.find((e) => e.event.id === selected)!);
  data.role = role;
  data.events = events.map((e) => ({
    id: e.event.id,
    name: e.event.name,
    role,
  }));
  data.metrics.active = data.participants.filter(
    (p) =>
      p.status === "Ativo" && p.online && data.event.status !== "Encerrado",
  ).length;
  data.metrics.participants = data.participants.length;
  data.participants.forEach((p) => {
    p.reports = data.cases.filter((c) => c.reported.id === p.id).length;
  });
  data.cases.forEach((c) => {
    c.reported = structuredClone(
      data.participants.find((p) => p.id === c.reported.id)!,
    );
    if (c.reporter)
      c.reporter = structuredClone(
        data.participants.find((p) => p.id === c.reporter!.id)!,
      );
  });
  if (role === "OPERATOR") {
    data.cases = [];
    data.blockSignals = [];
    data.metrics.blocks = null;
    data.participants.forEach((p) => {
      p.reason = "";
      p.reports = null;
      p.blocks = null;
    });
  }
  return data;
}
export const adminMock = {
  reset,
  setRole(value: string) {
    if (!["ADMIN", "MODERATOR", "OPERATOR"].includes(value))
      throw new Error("Papel inválido.");
    role = value;
  },
  async request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
    if (path === "event-admin/") {
      if (method === "POST") {
        const id = (body as { event: string }).event;
        if (!events.some((e) => e.event.id === id))
          throw new Error("Evento inexistente.");
        selected = id;
      }
      return snapshot() as T;
    }
    if (role === "OPERATOR")
      throw new Error("O operador não pode executar ações de moderação.");
    const data = events.find((e) => e.event.id === selected)!;
    const input = body as {
      action: string;
      reason: string;
      confirmed: boolean;
      category?: string;
    };
    const id = path.split("/")[2];
    const c = path.includes("/cases/")
      ? data.cases.find((c) => c.id === id)
      : undefined;
    const p = c?.reported || data.participants.find((p) => p.id === id);
    if (!p) throw new Error("Registro inexistente.");
    if (input.action !== "assume" && !input.reason?.trim())
      throw new Error("Informe a justificativa.");
    if (
      (input.action === "ban" || input.action === "reopen") &&
      role !== "ADMIN"
    )
      throw new Error("Ação exclusiva do administrador.");
    if (c && c.status === "Resolvida" && input.action !== "reopen")
      throw new Error("Reabra a ocorrência antes de alterá-la.");
    const participant = data.participants.find((x) => x.id === p.id)!;
    if (input.action === "ban") {
      if (!input.confirmed)
        throw new Error("Confirme explicitamente o banimento.");
      participant.status = "Banido";
      participant.reason = input.reason;
      participant.online = false;
    } else if (input.action === "suspend") {
      if (participant.status === "Banido")
        throw new Error("Participante banido.");
      participant.status = "Suspenso";
      participant.reason = input.reason;
      participant.online = false;
    } else if (input.action === "reactivate") {
      participant.status = "Ativo";
      participant.reason = "";
    } else if (input.action === "report") {
      const index = data.cases.length + 1;
      data.cases.unshift({
        id: `${selected}-case-${index}`,
        reference: `DEMO-${String(index).padStart(5, "0")}`,
        reason: input.category || "Ocorrência administrativa",
        description: input.reason,
        kind: "Administrativa",
        priority: 1,
        reported: participant,
        reporter: null,
        author: "Marcos Viana · Administrador",
        status: "Pendente",
        created: time(),
        closed: null,
        responsible: null,
        notes: [],
        history: [
          {
            id: mockId(),
            author: "Marcos Viana · Administrador",
            body: "Ocorrência administrativa criada: " + input.reason,
            created: time(),
          },
        ],
        evidence: [],
      });
    } else if (c && input.action === "assume") {
      c.status = "Em análise";
      c.responsible =
        "Você · " + (role === "ADMIN" ? "Administrador" : "Moderador");
    } else if (c && input.action === "resolve") {
      c.status = "Resolvida";
      c.closed = time();
    } else if (c && input.action === "reopen") {
      c.status = c.responsible ? "Em análise" : "Pendente";
      c.closed = null;
    } else if (c && input.action === "note") {
      c.notes.push({
        id: mockId(),
        author: "Você",
        body: input.reason,
        created: time(),
      });
    } else throw new Error("Ação inválida.");
    if (c) {
      const labels: Record<string, string> = {
        assume: "Ocorrência assumida",
        note: "Nota interna adicionada",
        resolve: "Ocorrência resolvida",
        reopen: "Ocorrência reaberta",
        ban: "Participante banido do evento",
        suspend: "Participante suspenso; caso em acompanhamento",
      };
      c.history.push({
        id: mockId(),
        author: "Você · " + role,
        body: labels[input.action] + (input.reason ? ": " + input.reason : ""),
        created: time(),
      });
    }
    return { ok: true } as T;
  },
};
export function mockEventInfo(id: string | null) {
  return events.find((e) => e.event.id === id)?.event;
}
