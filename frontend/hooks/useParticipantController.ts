import { useParticipantSocial } from "./useParticipantSocial";
import { useParticipantProfile } from "./useParticipantProfile";

import { useParticipantRouter } from "./useParticipantRouter";
import { useParticipantSync } from "./useParticipantSync";
import { useEffect, useRef, useState } from "react";
import { frontendConfig } from "../config";
import { api, ApiError, request } from "../backend-client";

import type { Context } from "../types";

import { clearImageCache } from "../CachedImage";

import { latestBirthYear } from "../birth-options";

import { mockEventInfo } from "../administration-mock";
import { mockPeople, initialChats, participantMock } from "../participant-mock";
import type {
  Person,
  PersonId,
  Profile,
  Filters,
  Message,
  Bootstrap,
  SessionData,
} from "../types";

import {
  stages,
  readPage,
  mockInterests,
  mockPurposes,
} from "../participant-pages";

export function useParticipantController() {
  const [serverData, setServerData] = useState<Bootstrap | null>(null);
  const serverDataRef = useRef(serverData);
  serverDataRef.current = serverData;
  const syncCursor = useRef<string | undefined>(undefined);
  const [demoData, setDemoData] = useState<Bootstrap | null>(() =>
    frontendConfig.isDemonstration ? participantMock.profileData() : null,
  );
  const interests = !frontendConfig.useMocks
    ? serverData?.profileTopics?.find((topic) => topic.key === "interests")
        ?.options || []
    : mockInterests;
  const purposes = !frontendConfig.useMocks
    ? serverData?.profileTopics?.find((topic) => topic.key === "purpose")
        ?.options || []
    : mockPurposes;
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
  const invitedEvent = new URLSearchParams(location.search).get("event");
  const invitePath = invite
    ? `join/${encodeURIComponent(invite)}/${invitedEvent ? `?event=${encodeURIComponent(invitedEvent)}` : ""}`
    : "";
  const [real] = useState(!frontendConfig.useMocks);
  const mockEvent = frontendConfig.useMocks
    ? mockEventInfo(new URLSearchParams(location.search).get("demoEvent"))
    : undefined;
  const [inviteName, setInviteName] = useState(mockEvent?.name || "");
  const canRegister = real
    ? Boolean(invite && inviteName)
    : !frontendConfig.isDemonstration;
  const [people, setPeople] = useState<Person[]>(real ? [] : mockPeople);
  const [remoteDiscovery, setRemoteDiscovery] = useState<Person[]>([]);
  const [authenticated, setAuthenticated] = useState(
    !real && !frontendConfig.isDemonstration,
  );
  const [ready, setReady] = useState(!real);
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const [serverActive, setServerActive] = useState(false);
  const [chatStates, setChatStates] = useState<Bootstrap["chatStates"]>({});

  const [eventName, setEventName] = useState(
    real ? "" : mockEvent?.name || "Conecta São Paulo",
  );

  const [profile, setProfile] = useState<Profile>(
    real
      ? {
          interests: [],
          purpose: "",
          first: "",
          last: "",
          month: "1",
          year: String(latestBirthYear),
          gender: "Prefiro não informar",
          bio: "",
        }
      : {
          interests: ["Música", "Viagens", "Gastronomia"],
          purpose: "Amizade",
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
          "/images/photo-1476514525535-07fb3b4ae5f1.jpg",
        ],
  );
  const [filters, setFilters] = useState<Filters>({
    min: 18,
    max: real ? 35 : 70,
    gender: "Todos",
    interests: [],
    purpose: "Networking",
  });

  const [seen, setSeen] = useState<PersonId[]>([]);
  const [liked, setLiked] = useState<PersonId[]>([]);
  const [chats, setChats] = useState<Record<string, Message[]>>(
    real ? {} : initialChats,
  );
  const chatsRef = useRef(chats);
  chatsRef.current = chats;
  const chatStatesRef = useRef(chatStates);
  chatStatesRef.current = chatStates;
  const blockedRef = useRef<string[]>([]);
  const [activeChat, setActiveChat] = useState<PersonId | null>(null);

  const [details, setDetails] = useState<Person | null>(null);

  const [match, setMatch] = useState<Person | null>(null);
  const [toast, setToast] = useState("");

  const [unread, setUnread] = useState<PersonId[]>(real ? [] : [3, 15, 31]);
  const [saved, setSaved] = useState<PersonId[]>([]);

  const imageScope = JSON.stringify([
    serverData?.event.id,
    serverActive,
    chatStates,
  ]);
  const previousImageScope = useRef<string | null>(null);
  useEffect(() => {
    if (!serverData) {
      previousImageScope.current = null;
      return;
    }
    if (
      previousImageScope.current !== null &&
      previousImageScope.current !== imageScope
    ) {
      clearImageCache();
    }
    previousImageScope.current = imageScope;
  }, [imageScope, Boolean(serverData)]);
  const notify = (text: string) => setToast(text);
  const { page, setPage, navigate, navigateBottom } = useParticipantRouter({
    real,
    authenticated,
    serverActive,
    adminMode,
    globalMode,
    contexts,
    mailbox,
    activeChat,
    setMailbox,
    setActiveChat,
    setAdminMode,
    setDetails,
    setMatch,
  });
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 3500);
    return () => clearTimeout(timer);
  }, [toast]);
  const applyData = (data: SessionData) => {
    setGlobalMode(data.navigation === "global");
    setContexts(data.navigation === "selection" ? data.contexts : null);
    if (data.navigation === "global" || data.navigation === "selection") {
      setAdminMode(false);
      return;
    }
    if (data.navigation === "administration") {
      setAdminMode(true);
      location.hash = `admin-${data.initialPage || "dashboard"}`;
      return;
    }
    setAdminMode(false);
    syncCursor.current = data.syncCursor;
    blockedRef.current = [];
    setServerData(data);
    setProfile({
      ...data.profile,
      residenceState: data.profile.residenceState || "",
      interests: data.profile.interests || [],
      purpose: data.profile.purpose || "",
      year: data.profile.year || String(latestBirthYear),
    });
    setPhotos(data.photos);
    setFilters(data.filters);

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
            await request(invitePath, "POST");
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
        }
      } catch (error) {
        if (active) {
          notify(
            error instanceof Error ? error.message : "Backend indisponível.",
          );
          location.hash = "login";
          setPage("login");
        }
      } finally {
        if (active) setReady(true);
      }
    })();
    return () => {
      active = false;
    };
  }, []);
  const loginSubmit = async (
    email: string,
    password: string,
    registering: boolean,
  ) => {
    if (!real) {
      setAuthenticated(true);
      location.hash = "perfil";
      setPage("perfil");
      notify("Você entrou na demonstração. Explore seu perfil!");
      return;
    }
    await run(async () => {
      await api.session();
      const data = await api.login(email, password, registering && canRegister);
      applyData(data);
      setAuthenticated(true);

      if (invite) history.replaceState(null, "", location.pathname);
      location.hash =
        data.navigation === "administration"
          ? `admin-${data.initialPage || "dashboard"}`
          : "perfil";
      setPage("perfil");
      notify("Você entrou na sua conta.");
    });
  };
  useParticipantSync({
    activeChat,
    adminMode,
    authenticated,
    blockedRef,
    busyRef,
    chatStatesRef,
    chatsRef,
    contexts,
    globalMode,
    mailbox,
    notify,
    page,
    real,
    serverData,
    serverDataRef,
    setChatStates,
    setChats,
    setPeople,
    setRemoteDiscovery,
    setServerActive,
    setServerData,
    setUnread,
    syncCursor,
  });

  const leave = async () => {
    if (real) {
      await api.logout();
      clearImageCache();
      setPeople([]);
      setPhotos([]);
      setChats({});
    }
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

    location.hash = "login";
    setPage("login");
  };
  const stage = stages.findIndex((s) => s.page === page);
  const eligibleFor = (f: Filters) =>
    people.filter(
      (p) =>
        p.age >= f.min &&
        p.age <= f.max &&
        (f.minHeight == null || (p.height != null && p.height >= f.minHeight)) &&
        (f.maxHeight == null || (p.height != null && p.height <= f.maxHeight)) &&
        (f.gender === "Todos" || p.gender === f.gender) &&
        (!f.interests.length ||
          f.interests.some((i) => p.interests.includes(i))),
    );
  const eligible = real ? remoteDiscovery : eligibleFor(filters);
  const candidate = eligible.find((p) => !seen.includes(p.id));
  const reviewParticipants = async () => {
    if (!real) {
      setSeen((old) => old.filter((id) => liked.includes(id) || String(id) in chats));
      return;
    }
    await run(async () => {
      const result = await request<{ count: number; data: Bootstrap }>("discovery/review/", "POST");
      applyData(result.data);
      if (!result.data.discovery.length) notify("Nenhum participante marcado como PASS corresponde aos filtros atuais.");
    });
  };

  const { saveProfile, applyFilters, removePhoto, uploadPhotos } =
    useParticipantProfile({
      applyData,
      navigate,
      notify,
      photos,
      profile,
      real,
      run,
      setFilters,
      setPhotos,
      setServerActive,
    });
  const {
    showDetails,
    toggleFavorite,
    select,
    openChat,
    openNotification,
    send,
  } = useParticipantSocial({
    activeChat,
    applyData,
    busyRef,
    chats,
    navigate,
    notify,
    people,
    real,
    run,
    saved,
    setActiveChat,
    setChats,
    setDetails,
    setLiked,
    setMailbox,
    setMatch,
    setSaved,
    setSeen,
    setUnread,
  });
  return {
    activeChat,
    adminMode,
    applyData,
    applyFilters,
    authenticated,
    busy,
    canRegister,
    candidate,
    chatStates,
    chats,
    contexts,
    demoData,
    details,
    eligible,
    eligibleFor,
    eventName,
    filters,
    globalMode,
    interests,
    inviteName,
    leave,
    liked,
    loginSubmit,
    mailbox,
    match,
    mockEvent,
    navigate,
    navigateBottom,
    noticeUnread,
    notify,
    openChat,
    openNotification,
    page,
    people,
    photos,
    profile,
    purposes,
    ready,
    reviewParticipants,
    real,
    removePhoto,
    run,
    saveProfile,
    saved,
    seen,
    select,
    send,
    serverData,
    setActiveChat,
    setAdminMode,
    setAuthenticated,
    setDemoData,
    setDetails,
    setMailbox,
    setMatch,
    setNoticeUnread,
    setPage,
    setPeople,
    setPhotos,
    setProfile,
    setRemoteDiscovery,
    setSeen,
    setServerActive,
    setServerData,
    setToast,
    showDetails,
    stage,
    toast,
    toggleFavorite,
    unread,
    uploadPhotos,
  };
}
export type ParticipantController = ReturnType<typeof useParticipantController>;
