import type { Filters, Person, ProfileTopic } from "./types";

export function topicSelections(filters: Filters, topic: ProfileTopic): string[] {
  return (filters.topics?.[topic.key] ?? (topic.key === "interests" ? filters.interests : []))
    .filter((value) => topic.options.includes(value)).slice(0, topic.filterMultiple ? undefined : 1);
}

export function normalizeTopicFilters(filters: Filters, topics: ProfileTopic[]): Filters {
  const selected = Object.fromEntries(topics.filter((topic) => topic.showInFilter)
    .map((topic) => [topic.key, topicSelections(filters, topic)]));
  return { ...filters, topics: selected, interests: selected.interests || [], purpose: "" };
}

export function matchesTopicFilters(person: Person, filters: Filters, topics: ProfileTopic[] | null): boolean {
  if (topics === null) return !filters.interests.length || filters.interests.some((value) => person.interests.includes(value));
  return topics.filter((topic) => topic.showInFilter).every((topic) => {
    const selected = topicSelections(filters, topic);
    const answers = topic.key === "interests" ? person.interests : person.topicAnswers?.[topic.key] || [];
    return selected.length === 0 || selected.some((value) => answers.includes(value));
  });
}
