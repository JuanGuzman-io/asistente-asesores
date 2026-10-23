// tests/web usa el formato de src/web: Prettier toma la configuración más cercana a cada archivo.
import { readFileSync } from "node:fs";
import { URL } from "node:url";

export default JSON.parse(readFileSync(new URL("../../src/web/.prettierrc", import.meta.url), "utf8"));
