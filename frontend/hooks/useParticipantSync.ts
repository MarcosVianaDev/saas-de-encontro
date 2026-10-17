import type { RefObject, Dispatch, SetStateAction } from "react";
import { useEffect } from "react";

import { api, ApiError } from "../backend-client";
import { mergeMessages, mergePeers } from "../participant-sync";
import { realtimeConnected, subscribeRealtime } from "../realtime";
import type { Context } from "../types";

import type { Person, PersonId, Message, Bootstrap } from "../types";
import { type Page } from "../participant-pages";

type Options = {
  activeChat: PersonId | null;
  adminMode: boolean;
  authenticated: boolean;
  blockedRef: RefObject<string[]>;
  busyRef: RefObject<boolean>;
  chatStatesRef: RefObject<
    Record<string, { active: boolean; blocked: boolean }>
  >;
  chatsRef: RefObject<Record<string, Message[]>>;
  contexts: Context[] | null;
  globalMode: boolean;
  mailbox: string;
  notify: (text: string) => void;
  page: Page;
  real: boolean;
  serverData: Bootstrap | null;
  serverDataRef: RefObject<Bootstrap | null>;
  setChatStates: Dispatch<
    SetStateAction<Record<string, { active: boolean; blocked: boolean }>>
  >;
  setChats: Dispatch<SetStateAction<Record<string, Message[]>>>;
  setPeople: Dispatch<SetStateAction<Person[]>>;
  setRemoteDiscovery: Dispatch<SetStateAction<Person[]>>;
  setServerActive: Dispatch<SetStateAction<boolean>>;
  setServerData: Dispatch<SetStateAction<Bootstrap | null>>;
  setUnread: Dispatch<SetStateAction<PersonId[]>>;
  syncCursor: RefObject<string | undefined>;
};

export function useParticipantSync({
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
}: Options) {
  useEffect(() => {
    if (
      !real ||
      !authenticated ||
      adminMode ||
      globalMode ||
      contexts ||
      !serverData?.event.id
    )
      return;
    let disposed = false;
    let pending = false;
    let pushed = false;
    let retryAfter = 0;
    let timer: number;
    const refresh = async () => {
      if (pending || disposed) return;
      pending = true;
      let more = false;
      let delay = (realtimeConnected() ? 60000 : 15000) + Math.random() * 3000;
      pushed = false;
      try {
        if (document.hidden) return;
        if (Date.now() < retryAfter) {
          delay = retryAfter - Date.now();
          return;
        }
        if (busyRef.current) {
          delay = 1000;
          return;
        }
        const delta = await api.sync(
          syncCursor.current,
          serverDataRef.current?.event.state,
        );
        if (disposed || busyRef.current) return;
        const merged = mergeMessages(chatsRef.current, delta);
        chatsRef.current = merged;
        setChats(merged);
        chatStatesRef.current = delta.chatStates;
        setChatStates(delta.chatStates);
        setUnread(delta.unread);
        blockedRef.current = delta.blocked.map(String);
        setPeople((old) => mergePeers(old, delta));
        setRemoteDiscovery((old) =>
          delta.status.socialAvailable
            ? old.filter(
                (person) =>
                  !blockedRef.current.includes(String(person.id)) &&
                  !delta.chatStates[person.id]?.blocked,
              )
            : [],
        );
        setServerData((old) => (old ? { ...old, ...delta.status } : old));
        setServerActive(delta.status.active);
        syncCursor.current = delta.cursor;
        more = delta.hasMore;
        if (
          !document.hidden &&
          page === "mensagens" &&
          mailbox === "messages" &&
          activeChat !== null
        ) {
          const ids = (merged[activeChat] || [])
            .filter((item) => item.unread && item.id)
            .slice(0, 100)
            .map((item) => item.id!);
          if (ids.length) {
            const acknowledgement = await api.readMessages(activeChat, ids);
            if (disposed) return;
            const read = new Set(acknowledgement.read);
            const next = {
              ...chatsRef.current,
              [activeChat]: (chatsRef.current[activeChat] || []).map((item) =>
                item.id && read.has(item.id)
                  ? { ...item, unread: false, updated: acknowledgement.updated }
                  : item,
              ),
            };
            chatsRef.current = next;
            setChats(next);
            if (!next[activeChat].some((item) => item.unread))
              setUnread((old) => old.filter((id) => id !== activeChat));
            more ||= ids.length === 100;
          }
        }
      } catch (error) {
        if (error instanceof ApiError && error.status === 429) {
          delay = 60000;
          retryAfter = Date.now() + delay;
          more = false;
          pushed = false;
        }
        if (!disposed)
          notify(
            error instanceof Error
              ? error.message
              : "Falha ao atualizar mensagens.",
          );
      } finally {
        pending = false;
        if (!disposed)
          timer = window.setTimeout(
            () => void refresh(),
            more || pushed ? 1000 : delay,
          );
      }
    };
    const visible = () => {
      if (!document.hidden && !pending) {
        clearTimeout(timer);
        void refresh();
      }
    };
    const unsubscribe = subscribeRealtime((update) => {
      if (
        !update.connected ||
        update.topics.some((topic) =>
          ["reconnected", "messages", "status"].includes(topic),
        )
      ) {
        if (document.hidden) return;
        if (pending) pushed = true;
        else if (!busyRef.current) {
          clearTimeout(timer);
          void refresh();
        } else {
          clearTimeout(timer);
          timer = window.setTimeout(() => void refresh(), 1000);
        }
      }
    });
    void refresh();
    document.addEventListener("visibilitychange", visible);
    return () => {
      disposed = true;
      unsubscribe();
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", visible);
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
    serverData?.event.id,
  ]);
  useEffect(() => {
    if (
      !real ||
      !authenticated ||
      adminMode ||
      globalMode ||
      contexts ||
      !serverData?.socialAvailable ||
      !["descobrir", "participantes", "filtros"].includes(page)
    )
      return;
    let disposed = false;
    let pending = false;
    const refresh = async () => {
      if (pending || document.hidden || busyRef.current) return;
      pending = true;
      try {
        const data = await api.catalog();
        if (!disposed && !busyRef.current) {
          if (data.profileTopics) setServerData((old) => old ? { ...old, profileTopics: data.profileTopics } : old);
          setPeople((old) =>
            mergePeers(
              old.filter((person) => person.id in chatStatesRef.current),
              {
                peers: data.people,
                blocked: blockedRef.current,
                chatStates: chatStatesRef.current,
              },
            ),
          );
          setRemoteDiscovery(
            data.discovery.filter(
              (person) => !blockedRef.current.includes(String(person.id)),
            ),
          );
        }
      } catch (error) {
        if (!disposed)
          notify(
            error instanceof Error
              ? error.message
              : "Falha ao atualizar participantes.",
          );
      } finally {
        pending = false;
      }
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 60000);
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
    serverData?.event.id,
    serverData?.socialAvailable,
  ]);
}
