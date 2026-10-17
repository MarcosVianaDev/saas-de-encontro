export type Page =
  | "login"
  | "perfil"
  | "filtros"
  | "descobrir"
  | "mensagens"
  | "participantes";
export const stages: { page: Page; title: string; description: string }[] = [
  {
    page: "login",
    title: "Boas-vindas",
    description: "Seu próximo encontro começa aqui.",
  },
  {
    page: "perfil",
    title: "Seu perfil",
    description: "Mostre um pouco de quem você é.",
  },
  {
    page: "filtros",
    title: "Suas preferências",
    description: "Encontre conexões com a sua vibe.",
  },
  {
    page: "descobrir",
    title: "Descobrir pessoas",
    description: "Uma boa conversa pode mudar tudo.",
  },
  {
    page: "mensagens",
    title: "Mensagens",
    description: "Transforme um match em uma história.",
  },
  {
    page: "participantes",
    title: "Pessoas do evento",
    description: "Faça parte dessa comunidade.",
  },
];
export const mockInterests = [
  "Música",
  "Viagens",
  "Tecnologia",
  "Gastronomia",
  "Esportes",
  "Arte",
  "Networking",
  "Outros",
];
export const mockPurposes = [
  "Networking",
  "Amizade",
  "Relacionamento",
  "Negócios",
  "Troca de ideias",
  "Outros",
];
export const readPage = (): Page =>
  stages.some((s) => s.page === location.hash.slice(1))
    ? (location.hash.slice(1) as Page)
    : "login";
