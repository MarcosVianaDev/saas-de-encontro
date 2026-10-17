import { request } from "./backend-client";
import type { SessionData } from "./types";

export const spaAudience = import.meta.env.VITE_SPA_AUDIENCE || "development";
export const separatedSpa = spaAudience !== "development";

export async function enterSpa() {
  const route = await request<{ audience: string; path: string }>(
    "frontend/route/",
  );
  location.replace(route.path);
}

export function routeOutsideSpa(data: SessionData) {
  if (!separatedSpa || spaAudience === "global") return false;
  const target =
    data.navigation === "administration"
      ? "event-manager"
      : data.navigation === "global"
        ? "global"
        : data.navigation === "selection"
          ? "login"
          : "participant";
  if (target === spaAudience) return false;
  // Return to the separate login/router, which asks the server for the SPA.
  location.replace("/");
  return true;
}

export function returnToLogin() {
  if (!separatedSpa) return false;
  location.replace("/");
  return true;
}
