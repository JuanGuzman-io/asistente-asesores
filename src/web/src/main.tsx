import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

const raiz = document.getElementById("root");
if (raiz) createRoot(raiz).render(<StrictMode />);
