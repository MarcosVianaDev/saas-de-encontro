import type { Bootstrap, Message, Person, SyncDelta } from "./types";

export function mergeMessages(chats: Bootstrap["chats"], delta: SyncDelta): Bootstrap["chats"] {
  const next = { ...chats };
  for (const peer of Object.keys(delta.chatStates)) next[peer] ??= [];
  const changed = new Map<string, Map<string, Message>>();
  for (const { peer, ...message } of delta.messages) {
    if (!changed.has(peer)) changed.set(peer, new Map((next[peer] || []).map(item => [item.id!, item])));
    const entries = changed.get(peer)!;
    const existing = entries.get(message.id);
    if (!existing?.updated || !message.updated || message.updated >= existing.updated)
      entries.set(message.id, message);
  }
  for (const [peer, entries] of changed) {
    next[peer] = [...entries.values()].sort((left, right) =>
      (left.created || "").localeCompare(right.created || "") || String(left.id).localeCompare(String(right.id)),
    );
  }
  return next;
}

export function mergePeers(people: Person[], delta: Pick<SyncDelta, "peers" | "blocked" | "chatStates">): Person[] {
  const hidden = new Set(delta.blocked.map(String));
  const next = new Map(people.filter(person => !hidden.has(String(person.id)) || person.id in delta.chatStates).map(person => [String(person.id), person]));
  for (const person of delta.peers) {
    const inaccessible = hidden.has(String(person.id)) || delta.chatStates[person.id]?.blocked;
    if (inaccessible && !(person.id in delta.chatStates)) continue;
    next.set(String(person.id), inaccessible ? { ...person, name: "Usuário bloqueado",
      image: "/images/profile-placeholder.svg", job: "", city: "", residenceState: "", gender: "", bio: "", interests: [], online: false, age: 0 } : person);
  }
  return [...next.values()];
}
