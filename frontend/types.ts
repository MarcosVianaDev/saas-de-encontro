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
  photoEvidence?: { id: string; url: string }[];
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
export type Message = {
  id?: string;
  unread?: boolean;
  text: string;
  mine: boolean;
  time: string;
};
export type Bootstrap = {
  registrationStatus?: string;
  onboardingComplete?: boolean;
  activated?: boolean;
  socialAvailable?: boolean;
  locationConsent?: boolean;
  presence?: string;
  location?: {
    retries: number;
    failed: boolean;
    exhausted: boolean;
    technicalInactive: boolean;
    nextDue: string | null;
    exceptionUntil: string | null;
  };
  profileFields?: {
    id: string;
    name: string;
    required: boolean;
    kind: string;
    version: number;
    options: string[];
  }[];
  navigation?: "participant";
  profile: Profile;
  photos: string[];
  publicPhotos?: string[];
  active: boolean;
  filters: Filters;
  people: Person[];
  discovery: Person[];
  chats: Record<string, Message[]>;
  chatStates: Record<string, { active: boolean; blocked: boolean }>;
  seen: PersonId[];
  liked: PersonId[];
  saved: PersonId[];
  event: {
    id: string;
    name: string;
    state?: string;
    status?: string;
    mode?: string;
    autoActivateParticipants?: boolean;
    ends?: string | null;
    locationInterval?: number;
    endingSoon?: boolean;
    readOnly?: boolean;
  };
};
export type SessionData =
  | Bootstrap
  | { navigation: "administration"; role: string; globalContext?: boolean }
  | { navigation: "global" }
  | { navigation: "selection"; contexts: Context[] };
export type Context = {
  key: string;
  navigation: string;
  name: string;
  event?: string;
};
