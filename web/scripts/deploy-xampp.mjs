// Build the dashboards as static files and publish them to XAMPP's htdocs.
//
//   npm run deploy:xampp                       -> C:\xampp\htdocs\driw  (http://localhost/driw/)
//   XAMPP_HTDOCS=D:\xampp\htdocs npm run deploy:xampp
//
// The target folder is replaced on every run, but only if an earlier run created it
// (it holds a .driw-deploy marker), so an unrelated folder of the same name is never deleted.

import { spawnSync } from "node:child_process";
import { cpSync, existsSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const FOLDER = "driw";
const htdocs = process.env.XAMPP_HTDOCS ?? "C:\\xampp\\htdocs";
const target = join(htdocs, FOLDER);
const webDir = resolve(import.meta.dirname, "..");
const outDir = join(webDir, "out");
const MARKER = ".driw-deploy";

if (!existsSync(htdocs)) {
  console.error(`XAMPP htdocs not found at ${htdocs}. Set XAMPP_HTDOCS to its location.`);
  process.exit(1);
}
if (existsSync(target) && readdirSync(target).length > 0 && !existsSync(join(target, MARKER))) {
  console.error(`${target} exists and was not created by this script; refusing to overwrite it.`);
  process.exit(1);
}

console.log(`Building static site for http://localhost/${FOLDER}/ ...`);
const build = spawnSync("npx", ["next", "build"], {
  cwd: webDir,
  stdio: "inherit",
  shell: true,
  env: { ...process.env, DRIW_TARGET: "xampp", DRIW_BASE_PATH: `/${FOLDER}` },
});
if (build.status !== 0) process.exit(build.status ?? 1);

rmSync(target, { recursive: true, force: true });
cpSync(outDir, target, { recursive: true });

// Apache: serve the site's own 404 page and keep the generated data fresh in browsers.
writeFileSync(
  join(target, ".htaccess"),
  [
    `ErrorDocument 404 /${FOLDER}/404.html`,
    // the link-preview image is exported without a file extension
    '<Files "opengraph-image">',
    "  ForceType image/png",
    "</Files>",
    "<IfModule mod_headers.c>",
    '  <FilesMatch "\\.(html|txt)$">',
    '    Header set Cache-Control "no-cache"',
    "  </FilesMatch>",
    "</IfModule>",
    "",
  ].join("\r\n"),
);
writeFileSync(join(target, MARKER), `Published by web/scripts/deploy-xampp.mjs on ${new Date().toISOString()}\r\n`);

console.log(`\nPublished to ${target}\nOpen http://localhost/${FOLDER}/`);
