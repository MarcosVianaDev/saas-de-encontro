import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { frontendConfig } from "../config";
import { readPage, type Page } from "../participant-pages";
import type { Context, Person, PersonId } from "../types";
type Setter<T> = Dispatch<SetStateAction<T>>;
type Options = {
  real: boolean;
  authenticated: boolean;
  serverActive: boolean;
  adminMode: boolean;
  globalMode: boolean;
  contexts: Context[] | null;
  mailbox: string;
  activeChat: PersonId | null;
  setMailbox: Setter<string>;
  setActiveChat: Setter<PersonId | null>;
  setAdminMode: Setter<boolean>;
  setDetails: Setter<Person | null>;
  setMatch: Setter<Person | null>;
};
export function useParticipantRouter({
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
}: Options) {
  const [page, setPage] = useState<Page>(
    frontendConfig.isDemonstration ? "login" : readPage,
  );
  const resolve = (next: Page): Page => {
    if (
      (real || frontendConfig.isDemonstration) &&
      next !== "login" &&
      !authenticated
    ) {
      next = "login";
    }
    if (
      real &&
      authenticated &&
      !serverActive &&
      !["login", "perfil", "filtros", "mensagens", "descobrir"].includes(next)
    )
      next = "perfil";
    if (real && authenticated && next === "login")
      next = serverActive ? "descobrir" : "perfil";
    return next;
  };
  const navigate = (requested: Page) => {
    const next = resolve(requested);
    if (next !== "mensagens") setActiveChat(null);
    location.hash = next;
    setPage(next);
    setDetails(null);
  };
  const navigateBottom = (next: Page) => {
    if (next === "mensagens") {
      if (
        page === "mensagens" &&
        !(mailbox === "messages" && activeChat !== null)
      ) {
        const tabs = ["messages", "notifications", "support"];
        setMailbox(tabs[(tabs.indexOf(mailbox) + 1) % tabs.length]);
      } else {
        setMailbox("messages");
      }
      setActiveChat(null);
    }
    navigate(next);
  };
  useEffect(() => {
    const onHash = () => {
      if (real && (adminMode || globalMode || contexts)) return;
      if (!real) setAdminMode(location.hash.startsWith("#admin-"));
      const requested = readPage();
      const next = resolve(requested);
      if (next !== requested) history.replaceState(null, "", `#${next}`);
      if (next !== "mensagens") setActiveChat(null);
      setPage(next);
      setDetails(null);
      setMatch(null);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [real, authenticated, serverActive, adminMode, globalMode, contexts]);

  return { page, setPage, navigate, navigateBottom };
}
