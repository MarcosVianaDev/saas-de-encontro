import { BIO_MIN_LENGTH, BIO_MAX_LENGTH } from "./profile-validation";
import type { Person, Message, Profile, Bootstrap } from "./types";
import type { Notice } from "./ParticipantExtras";

const photo = (id: string) => `/images/${id}.jpg`;
export const mockPeople: Person[] = [
  {
    id: 1,
    name: "Camila",
    age: 28,
    gender: "Mulheres",
    job: "Designer de produto",
    image: photo("photo-1544005313-94ddf0286df2"),
    interests: ["Música", "Viagens", "Gastronomia"],
    online: true,
    mutual: true,
  },
  {
    id: 2,
    name: "Lucas",
    age: 32,
    gender: "Homens",
    job: "Arquiteto",
    image: photo("photo-1500648767791-00dcc994a43e"),
    interests: ["Arte", "Gastronomia", "Networking"],
    online: true,
    mutual: true,
  },
  {
    id: 3,
    name: "Mariana",
    age: 26,
    gender: "Mulheres",
    job: "Fotógrafa",
    image: photo("photo-1524504388940-b1c1722653e1"),
    interests: ["Música", "Viagens", "Arte"],
    online: true,
    mutual: true,
  },
  {
    id: 4,
    name: "Rafael",
    age: 30,
    gender: "Homens",
    job: "Empreendedor",
    image: photo("photo-1519085360753-af0119f7cbe7"),
    interests: ["Tecnologia", "Esportes"],
    online: true,
    mutual: false,
  },
  {
    id: 5,
    name: "Aline",
    age: 27,
    gender: "Mulheres",
    job: "Publicitária",
    image: photo("photo-1524250502761-1ac6f2e30d43"),
    interests: ["Arte", "Música"],
    online: false,
    mutual: false,
  },
  {
    id: 6,
    name: "Thiago",
    age: 29,
    gender: "Homens",
    job: "Desenvolvedor",
    image: photo("photo-1506794778202-cad84cf45f1d"),
    interests: ["Tecnologia", "Viagens"],
    online: false,
    mutual: false,
  },
  {
    id: 7,
    name: "Beatriz",
    age: 24,
    gender: "Mulheres",
    job: "Produtora cultural",
    image: photo("photo-1531123897727-8f129e1688ce"),
    interests: ["Música", "Arte"],
    online: true,
    mutual: false,
  },
  {
    id: 8,
    name: "Carlos",
    age: 31,
    gender: "Homens",
    job: "Chef de cozinha",
    image: photo("photo-1535713875002-d1d0cf377fde"),
    interests: ["Gastronomia", "Networking"],
    online: false,
    mutual: false,
  },
  {
    id: 9,
    name: "Juliana",
    age: 28,
    gender: "Mulheres",
    job: "Jornalista",
    image: photo("photo-1534528741775-53994a69daeb"),
    interests: ["Viagens", "Gastronomia"],
    online: true,
    mutual: false,
  },
  {
    id: 10,
    name: "Pedro",
    age: 33,
    gender: "Homens",
    job: "Engenheiro",
    image: photo("photo-1507591064344-4c6ce005b128"),
    interests: ["Esportes", "Tecnologia"],
    online: false,
    mutual: false,
  },
  {
    id: 11,
    name: "Fernanda",
    age: 25,
    gender: "Mulheres",
    job: "Ilustradora",
    image: photo("photo-1526510747491-58f928ec870f"),
    interests: ["Arte", "Viagens"],
    online: false,
    mutual: false,
  },
  {
    id: 12,
    name: "Bruno",
    age: 28,
    gender: "Homens",
    job: "Músico",
    image: photo("photo-1463453091185-61582044d556"),
    interests: ["Música", "Gastronomia"],
    online: true,
    mutual: false,
  },
];
export const initialChats: Record<string, Message[]> = {
  3: [
    { text: "Oi! Adorei nosso papo no evento! 😊", mine: false, time: "14:30" },
  ],
  2: [
    { text: "Oi, Lucas! Está gostando do evento?", mine: true, time: "12:08" },
    { text: "Muito! Vamos no próximo painel?", mine: false, time: "12:10" },
  ],
  5: [{ text: "Também achei incrível!", mine: false, time: "Ontem" }],
  4: [{ text: "Conecta nos próximos workshops?", mine: false, time: "Ontem" }],
  7: [{ text: "Topo! Vamos sim! 🚀", mine: false, time: "Seg" }],
  6: [{ text: "Valeu pela indicação!", mine: false, time: "Seg" }],
  9: [{ text: "Foi muito bom te conhecer!", mine: false, time: "Dom" }],
  8: [{ text: "Até mais! 👋", mine: false, time: "Dom" }],
};

const additionalNames = [
  "Gabriela",
  "Mateus",
  "Alex",
  "Isabela",
  "Renata",
  "Gustavo",
  "Helena",
  "Diego",
  "Luiza",
  "Daniel",
  "Sam",
  "Patrícia",
  "Mônica",
  "André",
  "Clara",
  "Eduardo",
  "Robin",
  "Cristina",
  "Débora",
  "Felipe",
  "Nina",
  "Henrique",
  "Dani",
  "Sofia",
  "Teresa",
  "Miguel",
  "Joana",
  "Otávio",
  "Kim",
  "Carolina",
  "Lúcia",
  "Paulo",
  "Elisa",
  "Ricardo",
  "Ari",
  "Valéria",
  "Sandra",
  "Vitor",
];
const ages = [
  19, 21, 23, 25, 27, 29, 31, 34, 36, 38, 40, 43, 46, 49, 52, 55, 58, 61, 64,
  68,
];
const genders = [
  "Mulheres",
  "Homens",
  "Não binário",
  "Mulheres",
  "Prefiro não informar",
];
const interests = [
  "Música",
  "Viagens",
  "Tecnologia",
  "Gastronomia",
  "Esportes",
  "Arte",
  "Networking",
];
const jobs = [
  "Professora",
  "Pesquisador",
  "Artista",
  "Enfermeira",
  "Empreendedora",
  "Consultor",
  "Aposentada",
  "Analista",
];
const portraits = mockPeople.map((person) => person.image);
const surnames = [
  "Souza",
  "Oliveira",
  "Lima",
  "Costa",
  "Martins",
  "Almeida",
  "Santos",
  "Ferreira",
];
mockPeople.push(
  ...additionalNames.map((name, index): Person => ({
    id: index + 13,
    name,
    age: ages[index % ages.length],
    gender: genders[index % genders.length],
    job: jobs[index % jobs.length],
    image: portraits[index % portraits.length],
    interests: [
      interests[index % interests.length],
      interests[(index + 2) % interests.length],
      interests[(index + 4) % interests.length],
    ],
    online: index % 3 === 0,
    mutual: false,
  })),
);
export const mockFullName = (person: Person) =>
  `${person.name} ${surnames[(Number(person.id) - 1) % surnames.length]}`;
for (const person of mockPeople) {
  person.bio = `Gosto de ${person.interests.join(", ").toLowerCase()}. Quero trocar experiências, encontrar novas amizades e aproveitar as conversas e atividades deste evento.`;
  person.photos = [
    person.image,
    photo("photo-1476514525535-07fb3b4ae5f1"),
    photo("photo-1470229722913-7c0e2dbbafd3"),
  ];
  person.residenceState = ["SP", "RJ", "MG", "RS", "BA", "PE", "PR", "SC"][
    Number(person.id) % 8
  ];
}
for (const id of [15, 19, 25, 31, 40, 46]) {
  const person = mockPeople.find((person) => person.id === id)!;
  initialChats[id] = [
    {
      text: `Oi, ${person.name}! Foi ótimo conversar com você no evento.`,
      mine: true,
      time: "15:10",
    },
    {
      text: `Também gostei! Podemos conversar mais sobre ${person.interests[0].toLowerCase()}?`,
      mine: false,
      time: "15:12",
      unread: true,
    },
  ];
}
for (const person of mockPeople) {
  if (String(person.id) in initialChats) person.mutual = true;
}
export const mockReceivedLikeIds = [1, 10, 11, 13, 22, 34, 45, 50];
for (const id of mockReceivedLikeIds)
  mockPeople.find((person) => person.id === id)!.mutual = true;

export const mockAnnouncements = [
  {
    id: "demo-welcome",
    title: "Bem-vindos ao evento",
    body: "Aproveite para conhecer pessoas, conversar e participar das atividades. A equipe está disponível no suporte.",
  },
  {
    id: "demo-schedule",
    title: "Roda de conversa às 16h",
    body: "Encontre a equipe no espaço de convivência para uma conversa sobre viagens, cultura e novas conexões.",
  },
  {
    id: "demo-safety",
    title: "Respeito em todas as conexões",
    body: "Respeite os limites de cada participante. Se precisar de ajuda, procure a equipe do evento.",
  },
];
const created = (minutes: number) =>
  new Date(Date.now() - minutes * 60000).toISOString();
let notices: Notice[] = [
  {
    id: "demo-like-1",
    title: "Você recebeu um like",
    body: "Camila gostou do seu perfil. Veja quem curtiu você em Likes recebidos.",
    kind: "like",
    participant: "1",
    action: "#descobrir",
    created: created(2),
    read: false,
  },
  {
    id: "demo-match-3",
    title: "Novo match com Mariana",
    body: "Vocês se curtiram! Que tal começar uma conversa?",
    kind: "match",
    participant: "3",
    action: "#mensagens?participant=3",
    created: created(5),
    read: false,
  },
  {
    id: "demo-message-15",
    title: "Nova mensagem de Alex",
    body: initialChats[15][1].text,
    kind: "message",
    participant: "15",
    action: "#mensagens?participant=15",
    created: created(7),
    read: false,
  },
  ...mockAnnouncements.map((notice, index) => ({
    ...notice,
    kind: "announcement",
    action: "#mensagens",
    created: created(12 + index * 10),
    read: index === 2,
  })),
];
const threads = [
  {
    id: "demo-support-1",
    subject: "Dúvida sobre a programação",
    participant: "Você",
    messages: [
      {
        id: "demo-support-message-1",
        author: "Você",
        body: "Onde acontece a roda de conversa?",
        created: created(30),
      },
      {
        id: "demo-support-message-2",
        author: "Equipe do evento",
        body: "No espaço de convivência, às 16h. Esperamos você!",
        created: created(25),
      },
    ],
  },
];

export const mockCredentials = {
  email: "demonstracao@example.test",
  password: "Demonstracao123!",
};
const onboardingPhotos = [
  mockPeople[0].image,
  photo("photo-1476514525535-07fb3b4ae5f1"),
  photo("photo-1470229722913-7c0e2dbbafd3"),
];
let demoProfile: Profile = {
  first: "",
  last: "",
  month: "1",
  year: "",
  gender: "Prefiro não informar",
  bio: "",
  interests: [],
  purpose: "",
};
let onboardingComplete = false;
function profileData(): Bootstrap {
  return structuredClone({
    navigation: "participant",
    profile: demoProfile,
    photos: onboardingPhotos,
    active: onboardingComplete,
    activated: onboardingComplete,
    onboardingComplete,
    socialAvailable: onboardingComplete,
    locationConsent: true,
    filters: {
      min: 18,
      max: 70,
      gender: "Todos",
      interests: [],
      purpose: "Networking",
    },
    people: mockPeople,
    discovery: mockPeople,
    chats: initialChats,
    chatStates: Object.fromEntries(
      Object.keys(initialChats).map((id) => [
        id,
        { active: true, blocked: false },
      ]),
    ),
    seen: [],
    liked: [],
    saved: [],
    profileFields: [],
    profileTopics: [],
    event: {
      id: "demo-current",
      name: "Evento Conexões 2026",
      state: "RUNNING",
      mode: "ONLINE",
      autoActivateParticipants: true,
    },
  });
}

export const participantMock = {
  profileData,
  async saveProfile(profile: Profile) {
    if (
      !profile.first.trim() ||
      !profile.last.trim() ||
      profile.bio.trim().length < BIO_MIN_LENGTH ||
      profile.bio.trim().length > BIO_MAX_LENGTH ||
      onboardingPhotos.length !== 3
    ) {
      throw new Error(
        `Complete o nome, sobrenome, a descrição com ${BIO_MIN_LENGTH} a ${BIO_MAX_LENGTH} caracteres e as três fotos.`,
      );
    }
    demoProfile = structuredClone(profile);
    onboardingComplete = true;
    return profileData();
  },
  async upload(file: File) {
    if (
      !["image/jpeg", "image/png", "image/webp"].includes(file.type) ||
      file.size > 10 * 1024 * 1024
    )
      throw new Error("Use fotos JPG, PNG ou WebP de até 10 MB.");
    if (onboardingPhotos.length >= 3)
      throw new Error("Troque uma das três fotos antes de adicionar outra.");
    onboardingPhotos.push(URL.createObjectURL(file));
    return profileData();
  },
  async removePhoto(url: string) {
    const index = onboardingPhotos.indexOf(url);
    if (index >= 0) onboardingPhotos.splice(index, 1);
    if (url.startsWith("blob:")) URL.revokeObjectURL(url);
    return profileData();
  },
  addMatch(person: Person) {
    if (notices.some((notice) => notice.id === `demo-match-${person.id}`))
      return;
    notices.unshift({
      id: `demo-match-${person.id}`,
      title: `Novo match com ${person.name}`,
      body: "Vocês se curtiram. Comece uma conversa!",
      kind: "match",
      participant: String(person.id),
      action: `#mensagens?participant=${person.id}`,
      created: created(0),
      read: false,
    });
  },
  async request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
    if (path === "notifications/") {
      if (method === "POST") {
        const id = (body as { id: string }).id;
        notices = notices.map((notice) =>
          notice.id === id ? { ...notice, read: true } : notice,
        );
        return { ok: true } as T;
      }
      return structuredClone({
        items: notices,
        unread: notices.filter((notice) => !notice.read).length,
      }) as T;
    }
    if (path === "likes-received/")
      return structuredClone({
        count: mockReceivedLikeIds.length,
        hidden: 0,
        people: mockPeople.filter((person) =>
          mockReceivedLikeIds.includes(Number(person.id)),
        ),
        offers: [],
        instructions: "Os likes desta demonstração já estão disponíveis.",
      }) as T;
    if (["support/", "event-admin/support/"].includes(path)) {
      if (method === "GET") return structuredClone(threads) as T;
      const input = body as { thread?: string; body: string };
      let thread = threads.find((thread) => thread.id === input.thread);
      if (!thread) {
        thread = {
          id: `demo-support-${threads.length + 1}`,
          subject: input.body.slice(0, 80),
          participant: "Você",
          messages: [],
        };
        threads.push(thread);
      }
      thread.messages.push({
        id: `demo-support-message-${Date.now()}`,
        author: path.startsWith("event-admin") ? "Equipe do evento" : "Você",
        body: input.body,
        created: created(0),
      });
      return structuredClone(thread) as T;
    }
    throw new Error(`Operação indisponível na demonstração: ${path}`);
  },
};
