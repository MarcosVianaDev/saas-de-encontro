import { cp, mkdir, rm } from "node:fs/promises";
import { build } from "vite";

await rm(new URL("./dist/", import.meta.url), { recursive: true, force: true });
for (const mode of ["login", "participant", "event-manager", "global"]) {
  await build({ mode });
}
// Public assets contain images only; never copy source or other build output.
await mkdir(new URL("./dist/login/images/", import.meta.url), {
  recursive: true,
});
await cp(
  new URL("./public/images/", import.meta.url),
  new URL("./dist/login/images/", import.meta.url),
  { recursive: true },
);
