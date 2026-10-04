import type { Bootstrap, Person, PersonId } from "./types";

let csrfToken = "";
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
function errorText(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(errorText).join(" ");
  if (value && typeof value === "object")
    return Object.values(value).map(errorText).join(" ");
  return "Não foi possível concluir a operação.";
}
async function request<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const form = body instanceof FormData;
  const response = await fetch(`/api/${path}`, {
    method,
    credentials: "same-origin",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(body && !form ? { "Content-Type": "application/json" } : {}),
      ...(method !== "GET" ? { "X-CSRFToken": csrfToken } : {}),
    },
    body: body === undefined ? undefined : form ? body : JSON.stringify(body),
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok)
    throw new ApiError(
      data ? errorText(data) : `O backend retornou HTTP ${response.status}.`,
      response.status,
    );
  return data as T;
}
export const api = {
  async session() {
    const result = await request<{
      authenticated: boolean;
      csrfToken: string;
      demoEmail: string | null;
    }>("session/");
    csrfToken = result.csrfToken;
    return result;
  },
  async login(email: string, password: string, register = false) {
    const result = await request<{ csrfToken: string; data: Bootstrap }>(
      `auth/${register ? "register" : "login"}/`,
      "POST",
      { email, password },
    );
    csrfToken = result.csrfToken;
    return result.data;
  },
  async logout() {
    const result = await request<{ csrfToken: string }>("auth/logout/", "POST");
    csrfToken = result.csrfToken;
  },
  bootstrap: () => request<Bootstrap>("bootstrap/"),
  conversations: () =>
    request<Pick<Bootstrap, "chats" | "chatStates">>("conversations/"),
  saveProfile: (body: unknown) => request<Bootstrap>("profile/", "PUT", body),
  saveFilters: (body: unknown) => request<Bootstrap>("filters/", "PUT", body),
  decide: (id: PersonId, like: boolean) =>
    request<{ match: Person | null; data: Bootstrap }>(
      `interactions/${id}/`,
      "POST",
      { decision: like ? "LIKE" : "PASS" },
    ),
  favorite: (id: PersonId) =>
    request<{ saved: PersonId[] }>(`favorites/${id}/`, "POST"),
  person: (id: PersonId) => request<Person>(`participants/${id}/`),
  send: (id: PersonId, text: string) =>
    request<Bootstrap>(`conversations/${id}/messages/`, "POST", { text }),
  endMatch: (id: PersonId) => request<Bootstrap>(`matches/${id}/end/`, "POST"),
  async upload(file: File) {
    const form = new FormData();
    form.append("file", file);
    return request<{ photos: string[]; active: boolean }>(
      "profile/photos/",
      "POST",
      form,
    );
  },
  removePhoto: (url: string) =>
    request<{ photos: string[]; active: boolean }>(
      "profile/photos/",
      "DELETE",
      { url },
    ),
};
