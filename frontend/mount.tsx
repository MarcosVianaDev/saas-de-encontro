import { createRoot } from "react-dom/client";
import type { ComponentType } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./styles.css";
import "./toggles.css";

export function mount(App: ComponentType) {
  createRoot(document.getElementById("root")!).render(<App />);
}
