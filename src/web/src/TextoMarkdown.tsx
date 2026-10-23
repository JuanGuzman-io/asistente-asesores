// Markdown del servicio (D4 enmendado, C-6): formato sí, HTML y enlaces no (AC-1/C3).
// Solo se pintan los elementos de PERMITIDOS; un enlace queda como su texto y una imagen no se pinta.
// Sin rehype-raw, react-markdown muestra el HTML crudo como texto literal (S-2.4 lo cubre).
import Markdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";
import "./markdown.css";

const PERMITIDOS = [
  "p",
  "br",
  "strong",
  "em",
  "del",
  "h3",
  "h4",
  "ul",
  "ol",
  "li",
  "table",
  "thead",
  "tbody",
  "tr",
  "th",
  "td",
  "code",
  "pre",
  "blockquote",
  "hr",
];

// Los títulos del servicio quedan por debajo del h2 "Respuesta" o "Fuentes" de la pantalla.
const COMPONENTES: Components = {
  h1: ({ children }) => <h3>{children}</h3>,
  h2: ({ children }) => <h3>{children}</h3>,
  h3: ({ children }) => <h3>{children}</h3>,
  h4: ({ children }) => <h4>{children}</h4>,
  h5: ({ children }) => <h4>{children}</h4>,
  h6: ({ children }) => <h4>{children}</h4>,
  // La tabla va en un contenedor con desplazamiento horizontal para pantallas angostas.
  table: ({ children }) => (
    <div className="md-tabla">
      <table>{children}</table>
    </div>
  ),
};

export function TextoMarkdown({ texto }: { texto: string }) {
  return (
    <Markdown
      remarkPlugins={[remarkGfm, remarkBreaks]}
      allowedElements={PERMITIDOS}
      unwrapDisallowed
      components={COMPONENTES}
    >
      {texto}
    </Markdown>
  );
}
