import fs from "node:fs";
import path from "node:path";

const uiRoot = path.resolve(import.meta.dirname, "..");
const providerRoot = process.env.PYMSS_SOURCE_ROOT || path.resolve(uiRoot, "../pymss");
const catalog = JSON.parse(fs.readFileSync(path.join(providerRoot, "pymss/resources/model_catalog.json"), "utf8"));
const indexText = fs.readFileSync(path.join(uiRoot, "src/lib/model-advisory-index.ts"), "utf8");

const ids = catalog.models.map((model) => model.name);
const modelsMarker = "export const modelAdvisoryIndex = ";
const byIdMarker = " as const satisfies readonly ModelAdvisory[];";
const modelIndexStart = indexText.indexOf(modelsMarker);
const modelIndexEnd = indexText.indexOf(byIdMarker, modelIndexStart);
if (modelIndexStart === -1 || modelIndexEnd === -1) {
  console.error("Unable to locate generated modelAdvisoryIndex in model-advisory-index.ts");
  process.exit(1);
}
const modelIndexJson = indexText.slice(modelIndexStart + modelsMarker.length, modelIndexEnd);
const entryCount = JSON.parse(modelIndexJson).length;
const missing = ids.filter((id) => !indexText.includes(`"id": ${JSON.stringify(id)}`));
const megaCount = ids.filter((id) => id.startsWith("bs_mega_53stem_") && id.endsWith("_mvsep.ckpt")).length;
const indexedMegaCount = ids.filter(
  (id) => id.startsWith("bs_mega_53stem_") && id.endsWith("_mvsep.ckpt") && indexText.includes(`"id": ${JSON.stringify(id)}`),
).length;

if (entryCount !== ids.length || missing.length || megaCount !== 53 || indexedMegaCount !== 53) {
  console.error(JSON.stringify({ entryCount, catalogCount: ids.length, missing, megaCount, indexedMegaCount }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({ entryCount, catalogCount: ids.length, megaCount: indexedMegaCount }, null, 2));
