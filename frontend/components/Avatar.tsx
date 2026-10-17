import { CachedImage } from "../CachedImage";

import type { Person } from "../types";

export function Avatar({
  person,
  large = false,
}: {
  person: Person;
  large?: boolean;
}) {
  return (
    <span className={`avatar ${large ? "large" : ""}`}>
      <CachedImage src={person.image} alt={person.name} loading="lazy" />
      {person.online && <i className="online-dot" aria-label="Online" />}
    </span>
  );
}
