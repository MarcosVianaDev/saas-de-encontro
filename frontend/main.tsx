import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import { frontendConfig } from "./config";
import { api, ApiError, request } from "./backend-client";
import { Administration } from "./Administration";
import { GlobalAdministration } from "./GlobalAdministration";
import { Contexts } from "./Contexts";
import type { Context } from "./types";
import { ParticipantOnboarding } from "./ParticipantOnboarding";
import { SocialSafety } from "./SocialSafety";
import {
  NotificationCenter,
  SupportPanel,
  LikesReceived,
} from "./ParticipantExtras";
import { LocationControl } from "./LocationControl";
import { mockEventInfo } from "./administration-mock";
import type {
  Person,
  PersonId,
  Profile,
  Filters,
  Message,
  Bootstrap,
  SessionData,
} from "./types";

type Page =
  "login" | "perfil" | "filtros" | "descobrir" | "mensagens" | "participantes";
type IconName =
  | "people"
  | "search"
  | "heart"
  | "chat"
  | "user"
  | "filter"
  | "arrow"
  | "back"
  | "close"
  | "star"
  | "camera"
  | "plus"
  | "pin"
  | "work"
  | "check"
  | "send"
  | "grid";
function Icon({ name, size = 22 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    people: (
      <>
        <circle cx="12" cy="7" r="3" />
        <path d="M6 21v-3a6 6 0 0 1 12 0v3M3 10a2 2 0 1 0 0-4m18 4a2 2 0 1 1 0-4M2 20v-3a4 4 0 0 1 3-4m17 7v-3a4 4 0 0 0-3-4" />
      </>
    ),
    search: (
      <>
        <circle cx="10.5" cy="10.5" r="6.5" />
        <path d="m16 16 5 5" />
      </>
    ),
    heart: (
      <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z" />
    ),
    chat: <path d="M4 4h16v13H9l-5 4V4Zm4 5h8m-8 4h5" />,
    user: (
      <>
        <circle cx="12" cy="7" r="4" />
        <path d="M4 22v-2a8 8 0 0 1 16 0v2" />
      </>
    ),
    filter: (
      <>
        <path d="M3 6h18M3 12h18M3 18h18" />
        <circle cx="8" cy="6" r="2" />
        <circle cx="16" cy="12" r="2" />
        <circle cx="9" cy="18" r="2" />
      </>
    ),
    arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
    back: <path d="m15 5-7 7 7 7" />,
    close: <path d="m5 5 14 14M19 5 5 19" />,
    star: (
      <path d="m12 2 3 6.2 6.8 1-4.9 4.8 1.2 6.8-6.1-3.2-6.1 3.2 1.2-6.8L2.2 9.2l6.8-1L12 2Z" />
    ),
    camera: (
      <>
        <path d="M3 7h4l2-3h6l2 3h4v14H3V7Z" />
        <circle cx="12" cy="13" r="4" />
      </>
    ),
    plus: <path d="M12 4v16M4 12h16" />,
    pin: (
      <>
        <path d="M19 9c0 5-7 12-7 12S5 14 5 9a7 7 0 1 1 14 0Z" />
        <circle cx="12" cy="9" r="2" />
      </>
    ),
    work: (
      <>
        <rect x="3" y="7" width="18" height="14" rx="2" />
        <path d="M8 7V3h8v4M3 12h18m-9 0v3" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    send: <path d="m3 3 19 9-19 9 4-9-4-9Zm4 9h15" />,
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
const photo = (id: string) => `/images/${id}.jpg`;
const mockPeople: Person[] = [
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
const stages: { page: Page; title: string; description: string }[] = [
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
const interests = [
  "Música",
  "Viagens",
  "Tecnologia",
  "Gastronomia",
  "Esportes",
  "Arte",
  "Networking",
  "Outros",
];
const purposes = [
  "Networking",
  "Amizade",
  "Relacionamento",
  "Negócios",
  "Troca de ideias",
  "Outros",
];
const initialChats: Record<string, Message[]> = {
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
const readPage = (): Page =>
  stages.some((s) => s.page === location.hash.slice(1))
    ? (location.hash.slice(1) as Page)
    : "login";
function Avatar({
  person,
  large = false,
}: {
  person: Person;
  large?: boolean;
}) {
  return (
    <span className={`avatar ${large ? "large" : ""}`}>
      <img src={person.image} alt={person.name} loading="lazy" />
      {person.online && <i className="online-dot" aria-label="Online" />}
    </span>
  );
}
function App() {
  const [serverData, setServerData] = useState<Bootstrap | null>(null);
  const [mailbox, setMailbox] = useState("messages");
  const [noticeUnread, setNoticeUnread] = useState(0);
  const [globalMode, setGlobalMode] = useState(false);
  const [contexts, setContexts] = useState<Context[] | null>(null);
  const [adminMode, setAdminMode] = useState(
    frontendConfig.useMocks &&
      !new URLSearchParams(location.search).has("invite") &&
      location.hash.startsWith("#admin-"),
  );
  const invite = new URLSearchParams(location.search).get("invite");
  const inviteEventId = new URLSearchParams(location.search).get("event");
  const invitePath = invite
    ? `join/${encodeURIComponent(invite)}/${inviteEventId !== null ? `?event=${encodeURIComponent(inviteEventId)}` : ""}`
    : "";
  const [real] = useState(!frontendConfig.useMocks);
  const mockEvent = frontendConfig.useMocks
    ? mockEventInfo(new URLSearchParams(location.search).get("demoEvent"))
    : undefined;
  const [inviteName, setInviteName] = useState(mockEvent?.name || "");
  const canRegister = !real || Boolean(invite && inviteName);
  const [people, setPeople] = useState<Person[]>(real ? [] : mockPeople);
  const [remoteDiscovery, setRemoteDiscovery] = useState<Person[]>([]);
  const [authenticated, setAuthenticated] = useState(!real);
  const authenticatedRef = useRef(authenticated);
  authenticatedRef.current = authenticated;
  const [ready, setReady] = useState(!real);
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const [serverActive, setServerActive] = useState(false);
  const [chatStates, setChatStates] = useState<Bootstrap["chatStates"]>({});
  const [registering, setRegistering] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [eventName, setEventName] = useState(
    real ? "" : mockEvent?.name || "Conecta São Paulo",
  );

  const [page, setPage] = useState<Page>(readPage);
  const [profile, setProfile] = useState<Profile>(
    real
      ? {
          first: "",
          last: "",
          month: "1",
          year: "",
          gender: "Prefiro não informar",
          bio: "",
        }
      : {
          first: "Camila",
          last: "Souza",
          month: "6",
          year: "1998",
          gender: "Mulheres",
          bio: "Amo música, viagens e boas conversas. Aqui para conhecer pessoas incríveis e criar boas histórias neste evento!",
        },
  );
  const [photos, setPhotos] = useState<string[]>(
    real
      ? []
      : [
          mockPeople[0].image,
          mockPeople[2].image,
          photo("photo-1476514525535-07fb3b4ae5f1"),
        ],
  );
  const [filters, setFilters] = useState<Filters>({
    min: 18,
    max: 35,
    gender: "Todos",
    interests: [],
    purpose: "Networking",
  });
  const [draft, setDraft] = useState(filters);
  const [interestSearch, setInterestSearch] = useState("");
  const [seen, setSeen] = useState<PersonId[]>([]);
  const [liked, setLiked] = useState<PersonId[]>([]);
  const [chats, setChats] = useState<Record<string, Message[]>>(
    real ? {} : initialChats,
  );
  const [activeChat, setActiveChat] = useState<PersonId | null>(null);
  const [chatSearch, setChatSearch] = useState("");
  const [message, setMessage] = useState("");
  const [participantSearch, setParticipantSearch] = useState("");
  const [tab, setTab] = useState("Todos");
  const [compact, setCompact] = useState(false);
  const [details, setDetails] = useState<Person | null>(null);
  const [match, setMatch] = useState<Person | null>(null);
  const [toast, setToast] = useState("");
  const [loginForm, setLoginForm] = useState(real);
  const [unread, setUnread] = useState<PersonId[]>(real ? [] : [3]);
  const [saved, setSaved] = useState<PersonId[]>([]);
  const uploadRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const notify = (text: string) => setToast(text);
  const navigate = (next: Page) => {
    if (real && next !== "login" && !authenticated) {
      next = "login";
      setLoginForm(true);
    }
    if (
      real &&
      authenticated &&
      !serverActive &&
      !["login", "perfil", "filtros", "mensagens"].includes(next)
    )
      next = "perfil";
    if (real && authenticated && next === "login")
      next = serverActive ? "descobrir" : "perfil";
    if (next !== "mensagens") setActiveChat(null);
    location.hash = next;
    setPage(next);
    setDetails(null);
  };
  useEffect(() => {
    const onHash = () => {
      if (real && (adminMode || globalMode || contexts)) return;
      if (!real) setAdminMode(location.hash.startsWith("#admin-"));
      const next = readPage();
      if (real && authenticatedRef.current && next === "login") {
        location.hash = serverActive ? "descobrir" : "perfil";
        return;
      }
      setPage(next);
      setDetails(null);
      setMatch(null);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [real, authenticated, serverActive, adminMode, globalMode, contexts]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 3500);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "nearest" });
  }, [activeChat, chats]);
  useEffect(() => {
    const esc = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setDetails(null);
        setMatch(null);
      }
    };
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, []);
  useEffect(() => {
    if (!details && !match) return;
    const previous = document.activeElement as HTMLElement | null;
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]');
    const trap = (event: KeyboardEvent) => {
      if (event.key !== "Tab" || !dialog) return;
      const buttons = Array.from(
        dialog.querySelectorAll<HTMLElement>(
          "button:not(:disabled), input, a[href]",
        ),
      );
      const first = buttons[0];
      const last = buttons.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", trap);
    return () => {
      document.removeEventListener("keydown", trap);
      if (previous?.isConnected) previous.focus();
    };
  }, [details, match]);
  const applyData = (data: SessionData) => {
    setGlobalMode(data.navigation === "global");
    setContexts(data.navigation === "selection" ? data.contexts : null);
    if (data.navigation === "global" || data.navigation === "selection") {
      setAdminMode(false);
      return;
    }
    if (data.navigation === "administration") {
      setAdminMode(true);
      location.hash = "admin-dashboard";
      return;
    }
    setAdminMode(false);
    setServerData(data);
    setProfile(data.profile);
    setPhotos(data.photos);
    setFilters(data.filters);
    setDraft(data.filters);
    setPeople(data.people);
    setRemoteDiscovery(data.discovery);
    setChats(data.chats);
    setUnread(
      Object.keys(data.chats).filter((key) =>
        data.chats[key].some((m) => m.unread),
      ),
    );
    setChatStates(data.chatStates);
    setSeen(data.seen);
    setLiked(data.liked);
    setSaved(data.saved);
    setServerActive(data.active);
    setEventName(data.event.name);
    if (readPage() === "login") {
      location.hash = "perfil";
      setPage("perfil");
    }
  };
  const run = async (action: () => Promise<void>) => {
    if (busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    try {
      await action();
    } catch (error) {
      notify(
        error instanceof Error
          ? error.message
          : "Não foi possível conectar ao backend.",
      );
      if (error instanceof ApiError && error.status === 401) {
        setAuthenticated(false);
        location.hash = "login";
        setPage("login");
        setLoginForm(true);
      }
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  };
  useEffect(() => {
    if (!real) return;
    let active = true;
    void (async () => {
      try {
        if (invite) {
          const event = await request<{ id: string; name: string }>(invitePath);
          if (active) {
            setInviteName(event.name);
            setEventName(event.name);
          }
        }
        const session = await api.session();
        if (!active) return;
        if (session.authenticated) {
          if (invite) {
            await request(
              invitePath,
              "POST",
              inviteEventId !== null ? { event: inviteEventId } : undefined,
            );
            history.replaceState(null, "", location.pathname);
          }
          const data = await api.bootstrap();
          if (!active) return;
          applyData(data);
          setAuthenticated(true);
          if (data.navigation === "global" || data.navigation === "selection")
            return;
          if (data.navigation === "administration") {
            if (!location.hash.startsWith("#admin-"))
              location.hash = "admin-dashboard";
            return;
          }
          const next =
            data.active && readPage() !== "login" ? readPage() : "perfil";
          location.hash = next;
          setPage(next);
        } else {
          location.hash = "login";
          setPage("login");
          setLoginForm(true);
        }
      } catch (error) {
        if (active) {
          notify(
            error instanceof Error ? error.message : "Backend indisponível.",
          );
          location.hash = "login";
          setPage("login");
          setLoginForm(true);
        }
      } finally {
        if (active) setReady(true);
      }
    })();
    return () => {
      active = false;
    };
  }, []);
  const loginSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!real) {
      navigate("perfil");
      notify("Você entrou na demonstração. Explore seu perfil!");
      return;
    }
    await run(async () => {
      await api.session();
      const data = await api.login(email, password, registering && canRegister);
      applyData(data);
      setAuthenticated(true);
      setPassword("");
      if (invite) history.replaceState(null, "", location.pathname);
      location.hash =
        data.navigation === "administration" ? "admin-dashboard" : "perfil";
      setPage("perfil");
      notify("Você entrou na sua conta.");
    });
  };
  useEffect(() => {
    if (!real || !authenticated || adminMode || globalMode || contexts) return;
    let disposed = false;
    const refresh = async () => {
      if (busyRef.current || document.hidden) return;
      try {
        if (
          page === "mensagens" &&
          mailbox === "messages" &&
          activeChat !== null
        )
          await request(`conversations/${activeChat}/messages/`);
        const data = await request<Bootstrap>("bootstrap/");
        if (!disposed && !busyRef.current) {
          setChats(data.chats);
          setChatStates(data.chatStates);
          setUnread(
            Object.keys(data.chats).filter((key) =>
              data.chats[key].some((m) => m.unread),
            ),
          );
          setServerData(data);
          setServerActive(data.active);
          setPeople(data.people);
          setRemoteDiscovery(data.discovery);
        }
      } catch (error) {
        if (!disposed)
          notify(
            error instanceof Error
              ? error.message
              : "Falha ao atualizar mensagens.",
          );
      }
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => {
      disposed = true;
      clearInterval(timer);
    };
  }, [
    real,
    authenticated,
    adminMode,
    globalMode,
    contexts,
    page,
    mailbox,
    activeChat,
  ]);
  const saveProfile = async (event: FormEvent) => {
    event.preventDefault();
    if (profile.bio.trim().length < 50) {
      notify("A bio precisa de pelo menos 50 caracteres.");
      return;
    }
    if (photos.length < 3) {
      notify("Adicione pelo menos 3 fotos para continuar.");
      return;
    }
    if (!real) {
      navigate("filtros");
      return;
    }
    await run(async () => {
      applyData(await api.saveProfile(profile));
      navigate("descobrir");
      notify("Perfil salvo.");
    });
  };
  const applyFilters = async () => {
    if (!real) {
      setFilters({ ...draft, interests: [...draft.interests] });
      navigate("descobrir");
      notify("Preferências aplicadas. Boas conexões!");
      return;
    }
    await run(async () => {
      applyData(await api.saveFilters(draft));
      navigate("descobrir");
      notify("Preferências salvas no backend.");
    });
  };
  const showDetails = async (person: Person) => {
    if (!real) {
      setDetails(person);
      return;
    }
    await run(async () => setDetails(await api.person(person.id)));
  };
  const toggleFavorite = async (person: Person) => {
    if (real) {
      await run(async () => {
        const result = await api.favorite(person.id);
        setSaved(result.saved);
        notify("Favoritos atualizados.");
      });
      return;
    }
    setSaved((old) =>
      old.includes(person.id)
        ? old.filter((id) => id !== person.id)
        : [...old, person.id],
    );
    notify(
      saved.includes(person.id)
        ? "Perfil removido dos favoritos."
        : "Perfil salvo nos favoritos desta sessão.",
    );
  };
  const removePhoto = async (url: string, index: number) => {
    if (real) {
      await run(async () => {
        const result = await api.removePhoto(url);
        setPhotos(result.photos);
        setServerActive(result.active);
      });
      return;
    }
    if (url.startsWith("blob:")) URL.revokeObjectURL(url);
    setPhotos((old) => old.filter((_, i) => i !== index));
  };
  const uploadPhotos = async (files: File[]) => {
    const valid = files.filter(
      (f) =>
        ["image/jpeg", "image/png", "image/webp"].includes(f.type) &&
        f.size <= 10 * 1024 * 1024,
    );
    if (valid.length !== files.length)
      notify("Use fotos JPG, PNG ou WebP de até 10 MB.");
    if (valid.length + photos.length > 10)
      notify("Você pode adicionar até 10 fotos.");
    const selected = valid.slice(0, 10 - photos.length);
    if (!real) {
      setPhotos((old) => [
        ...old,
        ...selected.map((f) => URL.createObjectURL(f)),
      ]);
      return;
    }
    await run(async () => {
      for (const file of selected) {
        const result = await api.upload(file);
        setPhotos(result.photos);
        setServerActive(result.active);
      }
    });
  };
  const leave = async () => {
    if (real) {
      await api.logout();
      setPeople([]);
      setPhotos([]);
      setChats({});
    }
    authenticatedRef.current = false;
    setAuthenticated(false);
    setAdminMode(false);
    setGlobalMode(false);
    setContexts(null);
    setServerData(null);
    setServerActive(false);
    setRemoteDiscovery([]);
    setChatStates({});
    setActiveChat(null);
    setUnread([]);
    setNoticeUnread(0);
    setMailbox("messages");
    setDetails(null);
    setMatch(null);
    setMessage("");
    setEmail("");
    setPassword("");
    setRegistering(false);
    setLoginForm(real);
    location.hash = "login";
    setPage("login");
  };
  const stage = stages.findIndex((s) => s.page === page);
  const eligibleFor = (f: Filters) =>
    people.filter(
      (p) =>
        p.age >= f.min &&
        p.age <= f.max &&
        (f.gender === "Todos" || p.gender === f.gender) &&
        (!f.interests.length ||
          f.interests.some((i) => p.interests.includes(i))),
    );
  const eligible = real ? remoteDiscovery : eligibleFor(filters);
  const candidate = eligible.find((p) => !seen.includes(p.id));
  const select = async (person: Person, like: boolean) => {
    if (real) {
      await run(async () => {
        const result = await api.decide(person.id, like);
        applyData(result.data);
        if (result.match) setMatch(result.match);
        else if (like) notify(`Seu like para ${person.name} foi enviado 💜`);
      });
      return;
    }
    setSeen((old) => [...new Set([...old, person.id])]);
    if (like) {
      setLiked((old) => [...new Set([...old, person.id])]);
      if (person.mutual) {
        setChats((old) => ({ ...old, [person.id]: old[person.id] || [] }));
        setMatch(person);
      } else notify(`Seu like para ${person.name} foi enviado 💜`);
    }
  };
  const openChat = (id: PersonId) => {
    setActiveChat(id);
    setUnread((old) => old.filter((item) => item !== id));
    navigate("mensagens");
  };
  const send = async (event: FormEvent) => {
    event.preventDefault();
    if (!message.trim() || activeChat === null) return;
    if (real) {
      await run(async () => {
        applyData(await api.send(activeChat, message.trim()));
        setMessage("");
      });
      return;
    }
    const entry = {
      text: message.trim(),
      mine: true,
      time: new Intl.DateTimeFormat("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date()),
    };
    setChats((old) => ({
      ...old,
      [activeChat]: [...(old[activeChat] || []), entry],
    }));
    setMessage("");
  };
  const shownParticipants = people.filter(
    (p) =>
      p.name
        .toLocaleLowerCase("pt-BR")
        .includes(participantSearch.toLocaleLowerCase("pt-BR")) &&
      (tab === "Todos" ||
        (tab === "Online" && p.online) ||
        (tab === "Matches" && p.id in chats)),
  );
  if (authenticated && contexts)
    return (
      <Contexts
        contexts={contexts}
        onSelect={applyData}
        onLogout={() => void run(leave)}
      />
    );
  if (authenticated && globalMode)
    return <GlobalAdministration onSelect={applyData} onLogout={leave} />;
  if (
    real &&
    authenticated &&
    !adminMode &&
    serverData &&
    serverData.onboardingComplete === false &&
    !serverData.event.readOnly
  )
    return (
      <ParticipantOnboarding
        data={serverData}
        onComplete={(d) => {
          applyData(d);
          location.hash = "perfil";
          setPage("perfil");
        }}
        onLogout={() => void run(leave)}
      />
    );
  if (adminMode && authenticated)
    return (
      <Administration
        mock={!real}
        onContext={
          real
            ? (global) => {
                void request<SessionData>(
                  "contexts/",
                  global ? "POST" : "GET",
                  global ? { key: "global" } : undefined,
                ).then(applyData);
              }
            : undefined
        }
        onLogout={leave}
      />
    );
  return (
    <div
      className={`workspace ${real ? "django-workspace" : "mock-workspace"} ${page === "login" ? "login-workspace" : "participant-workspace"} ${busy ? "is-busy" : ""}`}
      aria-busy={busy || !ready}
    >
      {!real && (
        <div className="backend-ribbon" role="status">
          <span>
            Demonstração ·{" "}
            {mockEvent ? `Ingresso em ${mockEvent.name}` : "Participante"}
          </span>
          <button
            onClick={() => {
              setAdminMode(true);
              setAuthenticated(true);
              location.hash = "admin-dashboard";
            }}
          >
            Explorar administração
          </button>
        </div>
      )}
      {real && (!ready || busy) && (
        <div className="backend-ribbon" role="status">
          {!ready ? "Conectando ao backend…" : busy ? "Salvando…" : "Conectado"}
        </div>
      )}
      {!real && (
        <aside className="sidebar">
          <a className="brand" href="#login">
            <span className="brand-icon">
              <Icon name="people" size={28} />
            </span>
            <span>
              Event<span className="brand-accent">Connect</span>
            </span>
          </a>
          <div className="event-label">
            <i className="live-dot" /> CONEXÕES QUE ACONTECEM
          </div>
          <h1>
            Pessoas reais.
            <br />
            <span>Encontros incríveis.</span>
          </h1>
          <p className="sidebar-intro">
            Encontre quem combina com você e aproveite cada momento do evento.
          </p>
          <nav className="stage-nav" aria-label="Etapas da experiência">
            {stages.map((s, index) => (
              <button
                key={s.page}
                className={page === s.page ? "selected" : ""}
                onClick={() => navigate(s.page)}
                aria-current={page === s.page ? "page" : undefined}
              >
                <span className="stage-number">{index + 1}</span>
                <span>
                  {s.title}
                  <small>{s.description}</small>
                </span>
                {page === s.page && <i className="nav-dot" />}
              </button>
            ))}
          </nav>
          <div className="sidebar-footer">
            <span className="preview-badge">PRÉVIA INTERATIVA</span>
            <p>Dados de exemplo para explorar a experiência.</p>
            <span>Feito para conectar. 💜</span>
          </div>
        </aside>
      )}
      <main className="main-area">
        {!real && (
          <div className="desktop-heading">
            <span>EXPERIÊNCIA DO PARTICIPANTE</span>
            <span className="event-tag">
              <i className="live-dot" /> Conecta São Paulo <span>/</span> Edição
              2026
            </span>
          </div>
        )}
        <div className="experience-layout">
          <section
            className={`app-screen ${page === "login" ? "login-screen" : ""}`}
            aria-label={stages[stage].title}
          >
            {page === "login" ? (
              <div className="login-content">
                <div className="login-top">
                  <span>SEU PRÓXIMO ENCONTRO</span>
                  {!real && <span className="login-pill">Conecta SP</span>}
                </div>
                <div className="login-hero">
                  <span className="hero-logo">
                    <Icon name="people" size={66} />
                  </span>
                  <h2>
                    Event<span>Connect</span>
                  </h2>
                  <p>
                    Pessoas reais,
                    <br />
                    experiências incríveis.
                  </p>
                  <div className="hero-line" />
                </div>
                {loginForm || (real && !canRegister) ? (
                  <form className="login-form" onSubmit={loginSubmit}>
                    <h3>
                      {inviteName
                        ? `Participar de ${inviteName}`
                        : "Que bom ter você aqui."}
                    </h3>
                    <p>
                      {real
                        ? registering
                          ? inviteName
                            ? "Sua conta será vinculada a este evento. Complete o perfil após o cadastro."
                            : "Crie sua conta para começar."
                          : inviteName
                            ? "Entre para vincular sua participação a este evento."
                            : "Entre com sua conta. Seu vínculo determina a navegação."
                        : "Acesso de demonstração, sem autenticação real."}
                    </p>
                    <label>
                      E-mail
                      <input
                        type="email"
                        autoComplete="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="voce@exemplo.com"
                        required
                      />
                    </label>
                    <label>
                      Senha
                      <input
                        type="password"
                        autoComplete={
                          registering ? "new-password" : "current-password"
                        }
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Sua senha"
                        minLength={6}
                        required
                      />
                    </label>
                    <button className="primary" type="submit">
                      {real
                        ? registering
                          ? "Criar conta"
                          : inviteName
                            ? "Entrar no evento"
                            : "Entrar"
                        : "Entrar na demonstração"}{" "}
                      <Icon name="arrow" size={18} />
                    </button>
                    {canRegister && (
                      <button
                        className="text-button light"
                        type="button"
                        onClick={() => setLoginForm(false)}
                      >
                        Voltar
                      </button>
                    )}
                    {real && canRegister && (
                      <button
                        className="text-button light"
                        type="button"
                        onClick={() => setRegistering(!registering)}
                      >
                        {registering ? "Já tenho uma conta" : "Criar uma conta"}
                      </button>
                    )}
                  </form>
                ) : (
                  <div className="login-actions">
                    <button
                      className="primary"
                      onClick={() => {
                        setRegistering(false);
                        setLoginForm(true);
                      }}
                    >
                      Entrar <Icon name="arrow" size={18} />
                    </button>
                    {canRegister && (
                      <button
                        className="secondary glass"
                        onClick={() => {
                          if (real) {
                            setRegistering(true);
                            setLoginForm(true);
                          } else navigate("perfil");
                        }}
                      >
                        Criar conta
                      </button>
                    )}
                    {canRegister && (
                      <button
                        className="demo-link"
                        onClick={() => {
                          if (real) {
                            setRegistering(true);
                            setLoginForm(true);
                          } else navigate("perfil");
                        }}
                      >
                        {real
                          ? "Criar uma nova conta"
                          : "Explorar demonstração"}{" "}
                        <Icon name="arrow" size={15} />
                      </button>
                    )}
                  </div>
                )}
                {canRegister && (
                  <div className="login-social-options">
                    <div className="or">
                      <span />
                      ou continue com
                      <span />
                    </div>
                    <button className="social" type="button" disabled>
                      <span className="google-mark">G</span> Continuar com
                      Google <small>Em breve</small>
                    </button>
                    <button className="social" type="button" disabled>
                      <span className="apple-mark">●</span> Continuar com Apple{" "}
                      <small>Em breve</small>
                    </button>
                  </div>
                )}
                <p className="login-terms">
                  Sua próxima boa conversa está aqui.
                  <br />
                  {!real && (
                    <span>
                      Prévia com dados fictícios. Nenhuma conta é criada.
                    </span>
                  )}
                </p>
              </div>
            ) : (
              <>
                {(page === "perfil" || page === "filtros") && !real && (
                  <div className="onboarding-progress">
                    <button
                      className="icon-button"
                      aria-label="Voltar"
                      onClick={() =>
                        navigate(page === "perfil" ? "descobrir" : "perfil")
                      }
                    >
                      <Icon name="back" />
                    </button>
                    <div className="progress-track">
                      <span
                        style={{ width: page === "perfil" ? "50%" : "100%" }}
                      />
                    </div>
                    <span>{page === "perfil" ? "1" : "2"} de 2</span>
                  </div>
                )}
                <div
                  className={`screen-content ${page === "descobrir" ? "discovery-content" : ""} ${page === "mensagens" && activeChat !== null ? "chat-content" : ""}`}
                >
                  {real && authenticated && serverData && (
                    <>
                      {serverData.event.endingSoon &&
                        !serverData.event.readOnly && (
                          <p className="event-banner">
                            O evento encerra às{" "}
                            {serverData.event.ends
                              ? new Date(
                                  serverData.event.ends,
                                ).toLocaleTimeString("pt-BR", {
                                  hour: "2-digit",
                                  minute: "2-digit",
                                })
                              : ""}
                            .
                          </p>
                        )}
                      {serverData.event.state === "PAUSED" && (
                        <section className="event-banner">
                          <strong>Evento pausado pela organização</strong>
                          <p>
                            Novas descobertas estão temporariamente
                            indisponíveis. Suas conversas e matches continuam
                            acessíveis.
                          </p>
                          <button onClick={() => navigate("mensagens")}>
                            Ir para mensagens
                          </button>
                        </section>
                      )}
                      {serverData.event.state === "OPEN" && (
                        <section className="event-banner">
                          <strong>O evento ainda não começou</strong>
                          <p>
                            A descoberta de participantes será liberada quando o
                            evento começar.
                          </p>
                          <button onClick={() => navigate("perfil")}>
                            Ver meu perfil
                          </button>
                        </section>
                      )}
                      {serverData.event.readOnly && (
                        <section className="event-banner">
                          <strong>Este evento foi encerrado</strong>
                          <p>
                            Perfil e conversas estão disponíveis somente para
                            consulta.
                          </p>
                          {page === "perfil" && (
                            <>
                              <h3>O que deseja fazer com seu perfil?</h3>
                              <button
                                onClick={() =>
                                  void run(async () => {
                                    applyData(
                                      await request<Bootstrap>(
                                        "profile/disposition/",
                                        "POST",
                                        { action: "persist" },
                                      ),
                                    );
                                    notify(
                                      "Perfil salvo para futuros eventos.",
                                    );
                                  })
                                }
                              >
                                Salvar perfil para futuros eventos
                              </button>
                              <details>
                                <summary>Excluir perfil deste evento</summary>
                                <p>
                                  Seu perfil deixará de aparecer socialmente.
                                  Dados sujeitos a obrigações legais, segurança
                                  ou preservação poderão permanecer pelo período
                                  aplicável.
                                </p>
                                <button
                                  onClick={(e) =>
                                    e.currentTarget
                                      .closest("details")
                                      ?.removeAttribute("open")
                                  }
                                >
                                  Cancelar
                                </button>
                                <button
                                  onClick={() =>
                                    void run(async () => {
                                      applyData(
                                        await request<Bootstrap>(
                                          "profile/disposition/",
                                          "POST",
                                          { action: "delete", confirmed: true },
                                        ),
                                      );
                                      notify("Exposição social removida.");
                                    })
                                  }
                                >
                                  Solicitar exclusão
                                </button>
                              </details>
                            </>
                          )}
                        </section>
                      )}
                      {serverData.registrationStatus === "PENDING" && (
                        <p className="event-banner">
                          Aguardando ativação. Procure a equipe para capturar a
                          foto do look e validar seu perfil.
                        </p>
                      )}
                      {serverData.registrationStatus === "INACTIVE" && (
                        <p className="event-banner">
                          Seu perfil está temporariamente desativado ou em
                          análise. Você pode falar com o Suporte em Mensagens.
                          <button
                            onClick={() => {
                              navigate("mensagens");
                              setMailbox("support");
                            }}
                          >
                            Falar com o suporte
                          </button>
                        </p>
                      )}
                      <LocationControl
                        data={serverData}
                        onSupport={() => {
                          navigate("mensagens");
                          setMailbox("support");
                        }}
                        onChanged={(d) => {
                          setServerData(d);
                          setServerActive(d.active);
                          setPeople(d.people);
                          setRemoteDiscovery(d.discovery);
                        }}
                      />
                      <NotificationCenter
                        visible={
                          page === "mensagens" && mailbox === "notifications"
                        }
                        onUnread={setNoticeUnread}
                      />
                      {page === "mensagens" && (
                        <>
                          <div className="mailbox-tabs">
                            <button onClick={() => setMailbox("messages")}>
                              Mensagens
                            </button>
                            <button onClick={() => setMailbox("notifications")}>
                              Notificações{" "}
                              {noticeUnread > 0 ? `(${noticeUnread})` : ""}
                            </button>
                            <button onClick={() => setMailbox("support")}>
                              Suporte
                            </button>
                          </div>
                          {mailbox === "support" && <SupportPanel />}
                        </>
                      )}
                    </>
                  )}
                  {page === "perfil" && (
                    <form
                      className="profile-form"
                      id="profile-form"
                      onSubmit={saveProfile}
                    >
                      <fieldset
                        disabled={Boolean(serverData?.event.readOnly)}
                        className="profile-readonly-fields"
                      >
                        <h2>
                          {real && serverData?.onboardingComplete
                            ? "Meu perfil"
                            : "Vamos criar seu perfil"}{" "}
                          <span className="tiny-spark">✦</span>
                        </h2>
                        <p className="subtitle">
                          Conte um pouco sobre você para
                          <br />
                          conectar com pessoas incríveis.
                        </p>
                        <div className="profile-avatar">
                          <img
                            src={photos[0] || "/images/profile-placeholder.svg"}
                            alt="Foto principal do seu perfil"
                          />
                          <button
                            type="button"
                            className="camera-button"
                            aria-label="Adicionar fotos ao perfil"
                            onClick={() => uploadRef.current?.click()}
                          >
                            <Icon name="camera" size={19} />
                          </button>
                        </div>
                        <div className="form-row">
                          <label className="field">
                            <span>Nome</span>
                            <input
                              value={profile.first}
                              onChange={(e) =>
                                setProfile({
                                  ...profile,
                                  first: e.target.value,
                                })
                              }
                              required
                              maxLength={150}
                            />
                          </label>
                          <label className="field">
                            <span>Sobrenome</span>
                            <input
                              value={profile.last}
                              onChange={(e) =>
                                setProfile({ ...profile, last: e.target.value })
                              }
                              required
                              maxLength={150}
                            />
                          </label>
                        </div>
                        <fieldset className="birth-field">
                          <legend>Nascimento</legend>
                          <div className="form-row">
                            <label>
                              Mês
                              <select
                                value={profile.month}
                                onChange={(e) =>
                                  setProfile({
                                    ...profile,
                                    month: e.target.value,
                                  })
                                }
                              >
                                {[
                                  "Janeiro",
                                  "Fevereiro",
                                  "Março",
                                  "Abril",
                                  "Maio",
                                  "Junho",
                                  "Julho",
                                  "Agosto",
                                  "Setembro",
                                  "Outubro",
                                  "Novembro",
                                  "Dezembro",
                                ].map((month, i) => (
                                  <option key={month} value={i + 1}>
                                    {month}
                                  </option>
                                ))}
                              </select>
                            </label>
                            <label>
                              Ano
                              <input
                                type="number"
                                min="1900"
                                max={new Date().getFullYear()}
                                value={profile.year}
                                required
                                onChange={(e) =>
                                  setProfile({
                                    ...profile,
                                    year: e.target.value,
                                  })
                                }
                              />
                            </label>
                          </div>
                        </fieldset>
                        <label className="field">
                          <span>Gênero</span>
                          <select
                            value={profile.gender}
                            onChange={(e) =>
                              setProfile({ ...profile, gender: e.target.value })
                            }
                          >
                            <option>Mulheres</option>
                            <option>Homens</option>
                            <option>Não binário</option>
                            <option>Prefiro não informar</option>
                          </select>
                        </label>
                        <label className="field bio-field">
                          <span>Sobre você</span>
                          <textarea
                            value={profile.bio}
                            onChange={(e) =>
                              setProfile({ ...profile, bio: e.target.value })
                            }
                            rows={3}
                            maxLength={200}
                            minLength={50}
                            required
                          />
                        </label>
                        <div className="field-help">
                          <span>Mínimo de 50 caracteres</span>
                          <span>{profile.bio.length}/200</span>
                        </div>
                        <div className="section-label">
                          <h3>Fotos do seu perfil</h3>
                          <span>{photos.length}/10</span>
                        </div>
                        <p className="microcopy">
                          As 3 primeiras são públicas. As demais, só após o
                          match.
                        </p>
                        <div className="photo-grid">
                          {photos.map((url, index) => (
                            <div className="photo-tile" key={url + index}>
                              <img
                                src={url}
                                alt={`Foto ${index + 1} do perfil`}
                              />
                              <button
                                className="remove-photo"
                                disabled={Boolean(
                                  real &&
                                  serverData?.activated &&
                                  serverData.publicPhotos?.includes(url),
                                )}
                                title={
                                  real &&
                                  serverData?.activated &&
                                  serverData.publicPhotos?.includes(url)
                                    ? "Esta foto faz parte do perfil aprovado para este evento e não pode ser alterada diretamente."
                                    : undefined
                                }
                                type="button"
                                aria-label={`Remover foto ${index + 1}`}
                                onClick={() => removePhoto(url, index)}
                              >
                                <Icon name="close" size={12} />
                              </button>
                              {index === 0 && <span>Principal</span>}
                            </div>
                          ))}
                          {photos.length < 10 && (
                            <button
                              type="button"
                              className="add-photo"
                              aria-label="Adicionar foto"
                              onClick={() => uploadRef.current?.click()}
                            >
                              <Icon name="plus" />
                            </button>
                          )}
                        </div>
                        <input
                          ref={uploadRef}
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          multiple
                          hidden
                          onChange={(e) => {
                            const files = Array.from(e.target.files || []);
                            e.target.value = "";
                            void uploadPhotos(files);
                          }}
                        />
                      </fieldset>
                      <section
                        className="profile-account"
                        aria-label="Conta do participante"
                      >
                        <h3>Conta</h3>
                        <button
                          type="button"
                          className="account-logout"
                          disabled={busy}
                          onClick={() => void run(leave)}
                        >
                          Sair da conta
                        </button>
                      </section>
                    </form>
                  )}
                  {page === "filtros" && !serverData?.event.readOnly && (
                    <div className="filters-form">
                      <h2>Definir filtros</h2>
                      <p className="subtitle">
                        Personalize suas preferências para
                        <br />
                        encontrar pessoas que combinam com você.
                      </p>
                      <section className="filter-card">
                        <h3>Faixa etária</h3>
                        <div className="range-value">
                          {draft.min} a {draft.max} anos
                        </div>
                        <div className="range-inputs">
                          <label>
                            De
                            <input
                              aria-label="Idade mínima"
                              type="range"
                              min="18"
                              max="70"
                              value={draft.min}
                              onChange={(e) =>
                                setDraft({
                                  ...draft,
                                  min: Math.min(
                                    Number(e.target.value),
                                    draft.max,
                                  ),
                                })
                              }
                            />
                          </label>
                          <label>
                            Até
                            <input
                              aria-label="Idade máxima"
                              type="range"
                              min="18"
                              max="70"
                              value={draft.max}
                              onChange={(e) =>
                                setDraft({
                                  ...draft,
                                  max: Math.max(
                                    Number(e.target.value),
                                    draft.min,
                                  ),
                                })
                              }
                            />
                          </label>
                        </div>
                      </section>
                      <section className="filter-card">
                        <h3>Gênero</h3>
                        <div className="chips">
                          {["Todos", "Mulheres", "Homens"].map((item) => (
                            <button
                              key={item}
                              aria-pressed={draft.gender === item}
                              className={`chip ${draft.gender === item ? "active" : ""}`}
                              onClick={() =>
                                setDraft({ ...draft, gender: item })
                              }
                            >
                              {item}
                            </button>
                          ))}
                        </div>
                      </section>
                      <section className="filter-card">
                        <div className="section-label">
                          <h3>Interesses</h3>
                          <span>Opcional</span>
                        </div>
                        <div className="search-field small">
                          <Icon name="search" size={17} />
                          <input
                            aria-label="Buscar interesses"
                            placeholder="Buscar interesses"
                            value={interestSearch}
                            onChange={(e) => setInterestSearch(e.target.value)}
                          />
                        </div>
                        <div className="chips">
                          {interests
                            .filter((item) =>
                              item
                                .toLowerCase()
                                .includes(interestSearch.toLowerCase()),
                            )
                            .map((item) => (
                              <button
                                key={item}
                                aria-pressed={draft.interests.includes(item)}
                                className={`chip ${draft.interests.includes(item) ? "active" : ""}`}
                                onClick={() =>
                                  setDraft({
                                    ...draft,
                                    interests: draft.interests.includes(item)
                                      ? draft.interests.filter(
                                          (i) => i !== item,
                                        )
                                      : [...draft.interests, item],
                                  })
                                }
                              >
                                {item}
                                <Icon
                                  name={
                                    draft.interests.includes(item)
                                      ? "check"
                                      : "plus"
                                  }
                                  size={13}
                                />
                              </button>
                            ))}
                        </div>
                        {!interests.some((item) =>
                          item
                            .toLowerCase()
                            .includes(interestSearch.toLowerCase()),
                        ) && (
                          <p className="microcopy">
                            Nenhum interesse encontrado.
                          </p>
                        )}
                        <p className="microcopy">
                          Mostrar pessoas com pelo menos um interesse
                          selecionado.
                        </p>
                      </section>
                      <section className="filter-card">
                        <h3>Finalidade no evento</h3>
                        <div className="chips">
                          {purposes.map((item) => (
                            <button
                              key={item}
                              aria-pressed={draft.purpose === item}
                              className={`chip ${draft.purpose === item ? "active" : ""}`}
                              onClick={() =>
                                setDraft({ ...draft, purpose: item })
                              }
                            >
                              {item}
                            </button>
                          ))}
                        </div>
                        <p className="microcopy">
                          Uma preferência para apresentar no seu perfil.
                        </p>
                      </section>
                      <div className="filter-summary">
                        <Icon name="people" size={18} />
                        <span>
                          {eligibleFor(draft).length} pessoas combinam com seus
                          filtros
                        </span>
                      </div>
                    </div>
                  )}
                  {page === "descobrir" &&
                    (!real || serverData?.socialAvailable) && (
                      <>
                        <div className="screen-title">
                          <h2>Descobrir pessoas</h2>
                          <button
                            className="icon-button purple"
                            aria-label="Alterar filtros"
                            onClick={() => {
                              setDraft(filters);
                              navigate("filtros");
                            }}
                          >
                            <Icon name="filter" />
                          </button>
                        </div>
                        <div className="discovery-meta">
                          <span>
                            <i className="live-dot" /> {eventName}
                          </span>
                          <span>
                            {
                              eligible.filter((p) => !seen.includes(p.id))
                                .length
                            }{" "}
                            para descobrir
                          </span>
                        </div>
                        {candidate ? (
                          <>
                            <div className="discovery-card">
                              {real && (
                                <SocialSafety
                                  person={candidate}
                                  onChanged={(d) => applyData(d)}
                                />
                              )}
                              <img
                                src={candidate.image}
                                alt={`Retrato de ${candidate.name}`}
                                className="discovery-photo"
                              />
                              <span className="online-pill">
                                {candidate.online
                                  ? "● Online agora"
                                  : "No evento"}
                              </span>
                              <div className="card-person">
                                <div className="person-heading">
                                  <h3>
                                    {candidate.name}, {candidate.age}{" "}
                                    <span
                                      className="verified"
                                      title="Participante validado"
                                    >
                                      <Icon name="check" size={13} />
                                    </span>
                                  </h3>
                                  <button
                                    className="info-button"
                                    aria-label={`Ver perfil de ${candidate.name}`}
                                    onClick={() => showDetails(candidate)}
                                  >
                                    i
                                  </button>
                                </div>
                                <p>
                                  <Icon name="work" size={14} />
                                  {candidate.job}
                                </p>
                                {(candidate.city || !real) && (
                                  <p>
                                    <Icon name="pin" size={14} />
                                    {candidate.city || "São Paulo, SP"}
                                  </p>
                                )}
                                <div className="person-tags">
                                  {candidate.interests.map((i) => (
                                    <span key={i}>{i}</span>
                                  ))}
                                </div>
                              </div>
                            </div>
                            <div className="discovery-actions">
                              <button
                                className="action-circle pass"
                                aria-label={`Passar ${candidate.name}`}
                                onClick={() => select(candidate, false)}
                              >
                                <Icon name="close" size={32} />
                              </button>
                              <button
                                className="action-circle like"
                                aria-label={`Curtir ${candidate.name}`}
                                onClick={() => select(candidate, true)}
                              >
                                <Icon name="heart" size={32} />
                              </button>
                            </div>
                            <div className="actions-caption">
                              <span>Passar</span>
                              <span>Gostei</span>
                            </div>
                          </>
                        ) : (
                          <div className="empty-state">
                            <Icon name="search" size={34} />
                            <h3>Você chegou ao fim por aqui.</h3>
                            <p>
                              Não há mais perfis com seus filtros atuais. Que
                              tal revisar suas preferências?
                            </p>
                            <button
                              className="primary"
                              onClick={() => {
                                setDraft(filters);
                                navigate("filtros");
                              }}
                            >
                              Revisar filtros
                            </button>
                            <button
                              className="text-button"
                              onClick={() => {
                                if (!real) setSeen([]);
                              }}
                            >
                              {real
                                ? "Histórico preservado no banco"
                                : "Rever perfis da demonstração"}
                            </button>
                          </div>
                        )}
                      </>
                    )}
                  {page === "mensagens" &&
                    (!real || mailbox === "messages") &&
                    (activeChat === null ? (
                      <>
                        <div className="screen-title">
                          <h2>Mensagens</h2>
                          <span className="count-badge">
                            {Object.keys(chats).length}
                          </span>
                        </div>
                        <p className="subtitle">
                          Boas histórias começam com um oi.
                        </p>
                        <div className="search-field">
                          <Icon name="search" size={18} />
                          <input
                            aria-label="Buscar conversas"
                            placeholder="Buscar conversas"
                            value={chatSearch}
                            onChange={(e) => setChatSearch(e.target.value)}
                          />
                        </div>
                        <div className="conversation-list">
                          {people
                            .filter(
                              (p) =>
                                p.id in chats &&
                                p.name
                                  .toLowerCase()
                                  .includes(chatSearch.toLowerCase()),
                            )
                            .map((p) => {
                              const last = chats[p.id].at(-1);
                              return (
                                <button
                                  className="conversation-row"
                                  key={p.id}
                                  onClick={() => openChat(p.id)}
                                >
                                  <Avatar person={p} />
                                  <span className="conversation-info">
                                    <strong>{p.name}</strong>
                                    <span>
                                      {last
                                        ? `${last.mine ? "Você: " : ""}${last.text}`
                                        : "Vocês combinaram! Envie um oi 💜"}
                                    </span>
                                  </span>
                                  <span className="conversation-time">
                                    {last?.time || "Agora"}
                                    {unread.includes(p.id) && <i>1</i>}
                                  </span>
                                </button>
                              );
                            })}
                        </div>
                        {!people.some(
                          (p) =>
                            p.id in chats &&
                            p.name
                              .toLowerCase()
                              .includes(chatSearch.toLowerCase()),
                        ) && (
                          <div className="empty-state">
                            <Icon name="chat" size={32} />
                            <h3>Nenhuma conversa encontrada</h3>
                            <p>Os seus matches aparecem aqui.</p>
                          </div>
                        )}
                        <div className="safe-chat">
                          <Icon name="heart" size={15} /> Conversas liberadas
                          quando o interesse é mútuo.
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="chat-heading">
                          <button
                            className="icon-button"
                            aria-label="Voltar às conversas"
                            onClick={() => setActiveChat(null)}
                          >
                            <Icon name="back" />
                          </button>
                          <Avatar
                            person={people.find((p) => p.id === activeChat)!}
                          />
                          <div>
                            <h2>
                              {people.find((p) => p.id === activeChat)!.name}
                            </h2>
                            <span>
                              {people.find((p) => p.id === activeChat)!.online
                                ? "Online agora"
                                : "Participante do evento"}
                            </span>
                          </div>
                          {real && chatStates[String(activeChat)]?.active && (
                            <button
                              className="secondary end-match"
                              disabled={busy}
                              onClick={() =>
                                void run(async () => {
                                  applyData(await api.endMatch(activeChat!));
                                  notify(
                                    "Match encerrado. Histórico preservado.",
                                  );
                                })
                              }
                            >
                              Encerrar match
                            </button>
                          )}
                        </div>
                        {real && (
                          <details className="conversation-menu">
                            <summary aria-label="Opções da conversa">⋮</summary>
                            <button
                              onClick={() =>
                                void showDetails(
                                  people.find((p) => p.id === activeChat)!,
                                )
                              }
                            >
                              Ver perfil
                            </button>
                            {chatStates[String(activeChat)]?.active && (
                              <button
                                onClick={() =>
                                  void toggleFavorite(
                                    people.find((p) => p.id === activeChat)!,
                                  )
                                }
                              >
                                {saved.includes(activeChat)
                                  ? "Desfavoritar"
                                  : "Favoritar"}
                              </button>
                            )}
                            <SocialSafety
                              person={people.find((p) => p.id === activeChat)!}
                              allowBlock
                              onChanged={(d) => applyData(d)}
                            />
                          </details>
                        )}
                        <div className="message-history">
                          <span className="day-divider">Hoje</span>
                          <p className="match-note">
                            {real &&
                            chatStates[String(activeChat)]?.active === false
                              ? "Match encerrado. Histórico em modo somente leitura."
                              : "Vocês deram match. A conversa começa aqui. 💜"}
                          </p>
                          {chats[activeChat]?.map((entry, index) => (
                            <div
                              key={index}
                              className={`message-bubble ${entry.mine ? "mine" : ""}`}
                            >
                              <p>{entry.text}</p>
                              <span>
                                {entry.time}
                                {entry.mine && " ✓"}
                              </span>
                            </div>
                          ))}
                          <div ref={bottomRef} />
                        </div>
                        {real && serverData?.event.readOnly ? (
                          <p>
                            Este evento terminou. A conversa está disponível
                            somente para consulta.
                          </p>
                        ) : (
                          <form className="message-composer" onSubmit={send}>
                            <input
                              aria-label="Mensagem"
                              disabled={
                                real &&
                                activeChat !== null &&
                                chatStates[String(activeChat)]?.active === false
                              }
                              placeholder={
                                real &&
                                activeChat !== null &&
                                chatStates[String(activeChat)]?.active === false
                                  ? "Conversa em modo somente leitura"
                                  : "Escreva sua mensagem…"
                              }
                              value={message}
                              maxLength={2000}
                              onChange={(e) => setMessage(e.target.value)}
                            />
                            <button
                              className="send-button"
                              aria-label="Enviar mensagem"
                              disabled={
                                !message.trim() ||
                                busy ||
                                (real &&
                                  activeChat !== null &&
                                  chatStates[String(activeChat)]?.active ===
                                    false)
                              }
                            >
                              <Icon name="send" size={20} />
                            </button>
                          </form>
                        )}
                      </>
                    ))}
                  {page === "participantes" &&
                    (!real || serverData?.socialAvailable) && (
                      <>
                        <div className="screen-title">
                          <h2>Participantes</h2>
                          {real && (
                            <details>
                              <summary>Likes recebidos</summary>
                              <LikesReceived
                                onPerson={(p) => void showDetails(p)}
                              />
                            </details>
                          )}
                          <button
                            className="icon-button purple"
                            aria-label={
                              compact
                                ? "Aumentar miniaturas"
                                : "Diminuir miniaturas"
                            }
                            aria-pressed={compact}
                            onClick={() => setCompact(!compact)}
                          >
                            <Icon name="grid" />
                          </button>
                        </div>
                        <p className="subtitle">
                          {people.length} pessoas, muitas possibilidades.
                        </p>
                        <div className="search-field">
                          <Icon name="search" size={18} />
                          <input
                            aria-label="Buscar participantes"
                            placeholder="Buscar participantes"
                            value={participantSearch}
                            onChange={(e) =>
                              setParticipantSearch(e.target.value)
                            }
                          />
                        </div>
                        <div
                          className="participant-tabs"
                          role="group"
                          aria-label="Filtrar participantes"
                        >
                          {["Todos", "Online", "Matches"].map((item) => (
                            <button
                              className={`chip ${tab === item ? "active" : ""}`}
                              aria-pressed={tab === item}
                              key={item}
                              onClick={() => setTab(item)}
                            >
                              {item}
                            </button>
                          ))}
                        </div>
                        <div
                          className={`participants-grid ${compact ? "compact" : ""}`}
                        >
                          {shownParticipants.map((p) => (
                            <button
                              className="participant-tile"
                              key={p.id}
                              onClick={() => showDetails(p)}
                            >
                              <Avatar person={p} large />
                              <strong>{p.name}</strong>
                              <span>{p.age} anos</span>
                              {p.id in chats && (
                                <span className="match-label">Seu match</span>
                              )}
                            </button>
                          ))}
                        </div>
                        {!shownParticipants.length && (
                          <div className="empty-state">
                            <Icon name="search" size={32} />
                            <h3>Ninguém por aqui</h3>
                            <p>Tente outro nome ou outra categoria.</p>
                          </div>
                        )}
                        <p className="participants-note">
                          Todos os participantes validados, independentemente
                          dos seus filtros de descoberta.
                        </p>
                      </>
                    )}
                </div>
                {(page === "perfil" || page === "filtros") &&
                  !serverData?.event.readOnly && (
                    <div className="onboarding-footer">
                      {page === "perfil" ? (
                        <button
                          type="submit"
                          form="profile-form"
                          className="primary"
                        >
                          Continuar <Icon name="arrow" size={19} />
                        </button>
                      ) : (
                        <button className="primary" onClick={applyFilters}>
                          Aplicar filtros <Icon name="arrow" size={19} />
                        </button>
                      )}
                    </div>
                  )}
                {[
                  "descobrir",
                  "mensagens",
                  "participantes",
                  "perfil",
                  "filtros",
                ].includes(page) && (
                  <nav className="bottom-nav" aria-label="Navegação principal">
                    {(
                      [
                        {
                          page: "descobrir",
                          text: "Descobrir",
                          icon: "search",
                        },
                        { page: "mensagens", text: "Mensagens", icon: "chat" },
                        {
                          page: "participantes",
                          text: "Participantes",
                          icon: "people",
                        },
                        { page: "perfil", text: "Perfil", icon: "user" },
                      ] as { page: Page; text: string; icon: IconName }[]
                    ).map((item) => (
                      <button
                        key={item.page}
                        className={
                          page === item.page ||
                          (page === "filtros" && item.page === "descobrir")
                            ? "active"
                            : ""
                        }
                        onClick={() => navigate(item.page)}
                        aria-current={
                          page === item.page ||
                          (page === "filtros" && item.page === "descobrir")
                            ? "page"
                            : undefined
                        }
                      >
                        <Icon name={item.icon} size={22} />
                        <span>{item.text}</span>
                        {item.page === "mensagens" &&
                          (unread.length > 0 || noticeUnread > 0) && (
                            <i className="nav-unread" />
                          )}
                      </button>
                    ))}
                  </nav>
                )}
              </>
            )}
          </section>
          {!real && (
            <aside className="context-panel">
              <span className="eyebrow">
                {String(stage + 1).padStart(2, "0")} / A SUA EXPERIÊNCIA
              </span>
              <h2>
                {[
                  "Toda conexão tem|um começo.",
                  "Seja você.|É o melhor jeito.",
                  "Sua vibe.|Suas conexões.",
                  "O próximo encontro|pode estar aqui.",
                  "Um match.|Muitas histórias.",
                  "Gente interessante.|No mesmo lugar.",
                ][stage]
                  .split("|")
                  .map((line, i) => (
                    <span key={line}>
                      {line}
                      {i === 0 && <br />}
                    </span>
                  ))}
              </h2>
              <p>
                {stages[stage].description} Descubra uma experiência feita para
                aproximar pessoas no mundo real.
              </p>
              <div className="event-preview">
                <span className="event-art">
                  <Icon name="people" size={32} />
                  <span>
                    conecta<span>2026</span>
                  </span>
                </span>
                <div>
                  <small>VOCÊ ESTÁ EM</small>
                  <strong>Conecta São Paulo</strong>
                  <span>
                    <Icon name="pin" size={13} /> São Paulo · edição 2026
                  </span>
                </div>
              </div>
              <div className="community">
                <div className="avatar-stack">
                  {people.slice(0, 4).map((p) => (
                    <img key={p.id} src={p.image} alt="" />
                  ))}
                </div>
                <span>
                  <strong>{people.length} pessoas</strong> prontas para se
                  conectar
                </span>
              </div>
              <div className="context-tip">
                <span>✦</span>
                <p>
                  {page === "perfil"
                    ? "Um perfil completo faz toda a diferença. Escolha fotos que contem a sua história."
                    : page === "filtros"
                      ? "Seus filtros podem mudar junto com você. Ajuste quando quiser."
                      : "As melhores conexões começam quando você se permite conhecer alguém novo."}
                </p>
              </div>
              <span className="context-footnote">
                Demonstração visual · dados fictícios
              </span>
            </aside>
          )}
        </div>
        {!real && (
          <footer className="desktop-footer">
            <span>EventConnect © 2026</span>
            <span>Conexões que saem da tela.</span>
            <button onClick={() => void run(leave)}>
              Voltar ao início <Icon name="arrow" size={14} />
            </button>
          </footer>
        )}
      </main>
      {toast && (
        <div className="toast" role="status">
          <Icon name="check" size={19} />
          {toast}
          <button aria-label="Fechar aviso" onClick={() => setToast("")}>
            <Icon name="close" size={15} />
          </button>
        </div>
      )}
      {details && (
        <div className="modal-backdrop" onClick={() => setDetails(null)}>
          <section
            role="dialog"
            aria-modal="true"
            aria-label={`Perfil de ${details.name}`}
            className="person-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              autoFocus
              className="modal-close"
              aria-label="Fechar perfil"
              onClick={() => setDetails(null)}
            >
              <Icon name="close" />
            </button>
            <img
              className="modal-photo"
              src={details.outfit || details.image}
              alt={details.name}
            />
            <div className="modal-body">
              {real && (
                <SocialSafety
                  person={details}
                  allowBlock
                  onChanged={(d) => applyData(d)}
                />
              )}

              {details.photos?.map((url, i) => (
                <img
                  className="modal-photo"
                  key={url}
                  src={url}
                  alt={`Foto pública ou pós-match ${i + 1}`}
                />
              ))}
              <h2>
                {details.name}, {details.age}{" "}
                <span className="verified">
                  <Icon name="check" size={13} />
                </span>
              </h2>
              <p className="modal-location">
                {details.city && (
                  <>
                    <Icon name="pin" size={15} />
                    {details.city} ·{" "}
                  </>
                )}
                {!real && !details.city && (
                  <>
                    <Icon name="pin" size={15} />
                    São Paulo, SP ·{" "}
                  </>
                )}
                {details.job}
              </p>
              {(details.bio || !real) && (
                <p>
                  {details.bio ||
                    "Gosto de boas conversas, novas experiências e pessoas que têm histórias para contar. Vamos nos conhecer?"}
                </p>
              )}
              <div className="chips">
                {details.interests.map((item) => (
                  <span className="chip" key={item}>
                    {item}
                  </span>
                ))}
              </div>
              <p className="microcopy">
                {details.id in chats
                  ? "Vocês já deram match. Que tal começar uma conversa?"
                  : "As fotos adicionais e o chat são liberados após um match."}
              </p>
              {details.id in chats ? (
                <button
                  className="primary"
                  onClick={() => openChat(details.id)}
                >
                  Enviar mensagem <Icon name="chat" size={18} />
                </button>
              ) : (
                <button
                  className="primary"
                  disabled={liked.includes(details.id)}
                  onClick={() => {
                    select(details, true);
                    setDetails(null);
                  }}
                >
                  {liked.includes(details.id) ? "Like enviado" : "Gostei"}{" "}
                  <Icon name="heart" size={18} />
                </button>
              )}
            </div>
          </section>
        </div>
      )}
      {match && (
        <div className="modal-backdrop">
          <section
            role="dialog"
            aria-modal="true"
            aria-label="Novo match"
            className="match-modal"
          >
            <button
              autoFocus
              className="modal-close"
              aria-label="Fechar match"
              onClick={() => setMatch(null)}
            >
              <Icon name="close" />
            </button>
            <span className="match-spark">✦</span>
            <h2>Deu match!</h2>
            <p>
              A conexão é mútua.
              <br />
              Que tal dar o primeiro oi?
            </p>
            <div className="match-avatars">
              <img
                src={photos[0] || "/images/profile-placeholder.svg"}
                alt="Seu perfil"
              />
              <span>
                <Icon name="heart" size={26} />
              </span>
              <img src={match.image} alt={match.name} />
            </div>
            <strong>Você e {match.name}</strong>
            <button
              className="primary"
              onClick={() => {
                openChat(match.id);
                setMatch(null);
              }}
            >
              Começar conversa <Icon name="chat" size={19} />
            </button>
            <button className="text-button" onClick={() => setMatch(null)}>
              Continuar descobrindo
            </button>
          </section>
        </div>
      )}
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
