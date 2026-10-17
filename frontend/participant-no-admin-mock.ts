// Management demo fixtures and operations must never enter the participant SPA.
export const mockEventInfo: typeof import("./administration-mock").mockEventInfo =
  () => undefined;
