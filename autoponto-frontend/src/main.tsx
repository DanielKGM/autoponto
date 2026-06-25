import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./app/App";
import "./scss/v4/main.scss";

createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
