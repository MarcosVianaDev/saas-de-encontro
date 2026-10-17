// This module replaces access-components in the participant build. Type-only
// imports preserve props checking without including management implementations.
import { createElement, useEffect } from "react";
const unavailable = () => {
  throw new Error("Esta interface exige outro pacote de acesso.");
};
export const Administration: typeof import("./Administration").Administration =
  unavailable;
export const GlobalAdministration: typeof import("./GlobalAdministration").GlobalAdministration =
  unavailable;
export const LoginPage: typeof import("./views/LoginPage").LoginPage = () => {
  useEffect(() => {
    location.replace("/");
  }, []);
  return createElement(
    "p",
    { role: "status" },
    "Redirecionando para o acesso…",
  );
};
