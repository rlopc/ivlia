// Spike: generate the contract types and the standalone validator.
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import Ajv2020 from "ajv/dist/2020.js";
import standaloneCode from "ajv/dist/standalone/index.js";
import { compile } from "json-schema-to-typescript";

const [schemaFile, outDir] = process.argv.slice(2);
const schema = JSON.parse(await readFile(schemaFile, "utf8"));
delete schema.discriminator.mapping;
schema.type = "object";
for (const def of Object.values(schema.$defs)) {
  for (const prop of Object.values(def.properties)) delete prop.title;
}

const ajv = new Ajv2020({
  code: { source: true, esm: true },
  discriminator: true,
});
const validate = ajv.compile(schema);
const types = await compile(schema, "ApiEvent", {
  bannerComment: "",
  additionalProperties: false,
});

await mkdir(outDir, { recursive: true });
await writeFile(path.join(outDir, "events.ts"), types);
await writeFile(
  path.join(outDir, "validate-event.js"),
  standaloneCode(ajv, validate),
);
