import type { Dispatch, SetStateAction, RefObject } from "react";

import { api, request } from "../backend-client";

import { type Notice } from "../ParticipantExtras";

import { participantMock } from "../participant-mock";
import type { Person, PersonId, Message, SessionData } from "../types";
import { type Page } from "../participant-pages";

type Options = {
  activeChat: PersonId | null;
  applyData: (data: SessionData) => void;
  busyRef: RefObject<boolean>;
  chats: Record<string, Message[]>;
  navigate: (next: Page) => void;
  notify: (text: string) => void;
  people: Person[];
  real: boolean;
  run: (action: () => Promise<void>) => Promise<void>;
  saved: PersonId[];
  setActiveChat: Dispatch<SetStateAction<PersonId | null>>;
  setChats: Dispatch<SetStateAction<Record<string, Message[]>>>;
  setDetails: Dispatch<SetStateAction<Person | null>>;
  setLiked: Dispatch<SetStateAction<PersonId[]>>;
  setMailbox: Dispatch<SetStateAction<string>>;
  setMatch: Dispatch<SetStateAction<Person | null>>;
  setSaved: Dispatch<SetStateAction<PersonId[]>>;
  setSeen: Dispatch<SetStateAction<PersonId[]>>;
  setUnread: Dispatch<SetStateAction<PersonId[]>>;
};

export function useParticipantSocial({
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
}: Options) {
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
        participantMock.addMatch(person);
      } else notify(`Seu like para ${person.name} foi enviado 💜`);
    }
  };
  const openChat = (id: PersonId) => {
    setMailbox("messages");
    setActiveChat(id);
    setUnread((old) => old.filter((item) => item !== id));
    navigate("mensagens");
  };
  const openNotification = (notice: Notice) => {
    if (!real) {
      const person = people.find(
        (person) => String(person.id) === notice.participant,
      );
      if (
        person &&
        ["match", "message"].includes(notice.kind || "") &&
        String(person.id) in chats
      ) {
        openChat(person.id);
      } else if (person && notice.kind === "like") {
        setDetails(person);
      } else {
        navigate("mensagens");
        setMailbox(notice.kind === "support" ? "support" : "notifications");
      }
      return;
    }
    void run(async () => {
      setActiveChat(null);
      if (notice.kind === "like") {
        navigate("participantes");
        // Fetch again: a pass may have revealed this like since the toast arrived.
        const notifications = await request<{ items: Notice[] }>(
          "notifications/",
        );
        const peer = notifications.items.find(
          (item) => item.id === notice.id,
        )?.participant;
        if (peer) setDetails(await api.person(peer));
        return;
      }
      if (notice.kind === "match") {
        const notifications = await request<{ items: Notice[] }>(
          "notifications/",
        );
        const peer = notifications.items.find(
          (item) => item.id === notice.id,
        )?.participant;
        if (peer) {
          applyData(await api.bootstrap());
          setMatch(await api.person(peer));
          return;
        }
      }
      if (notice.kind === "message") {
        const peer = new URLSearchParams(notice.action.split("?")[1] || "").get(
          "participant",
        );
        applyData(await api.bootstrap());
        if (peer) {
          openChat(peer);
          return;
        }
      }
      if (notice.action.split("?")[0] === "#descobrir") {
        applyData(await api.bootstrap());
        navigate("descobrir");
        return;
      }
      navigate("mensagens");
      setMailbox(notice.kind === "support" ? "support" : "notifications");
    });
  };
  const send = async (message: string): Promise<boolean> => {
    if (!message.trim() || activeChat === null || busyRef.current) return false;
    if (real) {
      let sent = false;
      await run(async () => {
        applyData(await api.send(activeChat, message.trim()));
        sent = true;
      });
      return sent;
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
    return true;
  };
  return {
    showDetails,
    toggleFavorite,
    select,
    openChat,
    openNotification,
    send,
  };
}
