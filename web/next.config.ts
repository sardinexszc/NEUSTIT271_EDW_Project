import type { NextConfig } from "next";

// XAMPP build (npm run deploy:xampp): plain static files served by Apache from a
// subfolder of htdocs, e.g. http://localhost/driw. Normal builds are unchanged.
const xampp = process.env.DRIW_TARGET === "xampp";
const basePath = xampp ? process.env.DRIW_BASE_PATH ?? "/driw" : undefined;

const nextConfig: NextConfig = {
  ...(xampp && {
    output: "export",
    basePath,
    // /driw/operations/ -> operations/index.html, which Apache serves without rewrite rules
    trailingSlash: true,
    images: { unoptimized: true },
  }),
};

export default nextConfig;
