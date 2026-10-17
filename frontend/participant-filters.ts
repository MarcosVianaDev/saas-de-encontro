import { matchesGender } from "./gender-filters";
import { matchesTopicFilters } from "./topic-filters";
import type { Filters, Person, ProfileTopic } from "./types";

export function matchingParticipants(people: Person[], filters: Filters, topics: ProfileTopic[] | null): Person[] {
  return people.filter((person) =>
    person.age >= filters.min && person.age <= filters.max &&
    (filters.minHeight == null || (person.height != null && person.height >= filters.minHeight)) &&
    (filters.maxHeight == null || (person.height != null && person.height <= filters.maxHeight)) &&
    matchesGender(person.gender, filters) && matchesTopicFilters(person, filters, topics),
  );
}
