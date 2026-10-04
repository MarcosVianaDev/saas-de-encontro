export type PersonId = string | number;
export type Person = {
  id: PersonId;
  name: string;
  age: number;
  gender: string;
  job: string;
  city?: string;
  image: string;
  interests: string[];
  online: boolean;
  mutual: boolean;
  bio?: string;
  photos?: string[];
  outfit?: string | null;
};
export type Profile = {
  first: string;
  last: string;
  month: string;
  year: string;
  gender: string;
  bio: string;
};
export type Filters = {
  min: number;
  max: number;
  gender: string;
  interests: string[];
  purpose: string;
};
export type Message = { text: string; mine: boolean; time: string };
export type Bootstrap = {
  profile: Profile;
  photos: string[];
  active: boolean;
  filters: Filters;
  people: Person[];
  discovery: Person[];
  chats: Record<string, Message[]>;
  chatStates: Record<string, { active: boolean; blocked: boolean }>;
  seen: PersonId[];
  liked: PersonId[];
  saved: PersonId[];
  event: { id: string; name: string };
};
