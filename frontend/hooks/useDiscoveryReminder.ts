import { useEffect, useRef, useState, type RefObject } from "react";
import { api } from "../backend-client";
import { matchingParticipants } from "../participant-filters";
import type { Page } from "../participant-pages";
import type { Filters, Person, ProfileTopic } from "../types";

const idleTime = 10 * 60 * 1000;
const refreshInterval = 60 * 1000;
const visitPrefix = "eventconnect-discovery-last-access:";
const explanationKey = "eventconnect-discovery-count-explained";
const visits = new Map<string, number>();
let explained = false;

function lastAccess(key: string): number | undefined {
  try {
    const stored = localStorage.getItem(key);
    const timestamp = stored === null ? NaN : Number(stored);
    if (Number.isFinite(timestamp) && timestamp >= 0 && timestamp <= Date.now()) return timestamp;
  } catch { /* Keep the timer working in memory if storage is unavailable. */ }
  return visits.get(key);
}

function recordAccess(key: string) {
  const timestamp = Date.now();
  visits.set(key, timestamp);
  try { localStorage.setItem(key, String(timestamp)); } catch { /* Use the in-memory timestamp. */ }
}

type Options = {
  enabled: boolean;
  eventId?: string;
  page: Page;
  real: boolean;
  filters: Filters;
  topics: ProfileTopic[] | null;
  people: Person[];
  busyRef: RefObject<boolean>;
  notify: (message: string) => void;
};

export function useDiscoveryReminder(options: Options) {
  const { enabled, eventId, page, real, busyRef } = options;
  const latest = useRef(options);
  latest.current = options;
  const [badge, setBadge] = useState<{ eventId: string; count: number } | null>(null);
  const filtersKey = JSON.stringify(options.filters);
  const topicsKey = JSON.stringify(options.topics);

  useEffect(() => {
    if (!enabled || !eventId) {
      setBadge(null);
      return;
    }
    const key = visitPrefix + eventId;
    let disposed = false;
    let running = false;
    let checkedAt: number | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;
    setBadge(null);
    if (lastAccess(key) === undefined) recordAccess(key);

    const tick = async () => {
      if (disposed || running) return;
      clearTimeout(timer);
      running = true;
      try {
        if (document.hidden) return;
        if (page === "descobrir") {
          recordAccess(key);
          setBadge(null);
          return;
        }
        const elapsed = Date.now() - (lastAccess(key) ?? Date.now());
        if (elapsed < idleTime) {
          setBadge(null);
          return;
        }
        if (busyRef.current || (checkedAt !== undefined && Date.now() - checkedAt < refreshInterval)) return;
        checkedAt = Date.now();
        const people = real ? (await api.catalog()).people : latest.current.people;
        if (disposed || document.hidden) return;
        if (Date.now() - (lastAccess(key) ?? Date.now()) < idleTime) {
          setBadge(null);
          return;
        }
        const count = matchingParticipants(people, latest.current.filters, latest.current.topics).length;
        setBadge({ eventId, count });
      } catch {
        if (!disposed) setBadge(null);
      } finally {
        running = false;
        if (!disposed) {
          const remaining = idleTime - (Date.now() - (lastAccess(key) ?? Date.now()));
          timer = setTimeout(() => void tick(), remaining > 0 ? Math.min(remaining, refreshInterval) : refreshInterval);
        }
      }
    };
    const onVisibility = () => {
      if (page === "descobrir") recordAccess(key);
      void tick();
    };
    const onStorage = (event: StorageEvent) => {
      if (event.key === key || event.key === null) void tick();
    };
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("focus", onVisibility);
    window.addEventListener("storage", onStorage);
    void tick();
    return () => {
      disposed = true;
      clearTimeout(timer);
      if (page === "descobrir") recordAccess(key);
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("focus", onVisibility);
      window.removeEventListener("storage", onStorage);
    };
  }, [enabled, eventId, page, real, filtersKey, topicsKey, busyRef]);

  const discoveryCount = enabled && page !== "descobrir" && badge && badge.eventId === eventId ? badge.count : 0;
  const explainDiscoveryCount = () => {
    if (discoveryCount <= 0) return;
    try { if (localStorage.getItem(explanationKey) === "1") return; } catch { /* Use the session fallback. */ }
    if (explained) return;
    explained = true;
    try { localStorage.setItem(explanationKey, "1"); } catch { /* Do not repeat it during this session. */ }
    latest.current.notify(`${discoveryCount} pessoas ainda combinam com suas preferências.`);
  };

  return { discoveryCount, explainDiscoveryCount };
}
