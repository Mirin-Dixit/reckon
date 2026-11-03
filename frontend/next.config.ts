import type { NextConfig } from "next";
import { localBackendOrigin } from "./lib/configuration";

// Validate before Next.js can inline public environment values into browser code.
const apiOrigin = localBackendOrigin(process.env.NEXT_PUBLIC_RAGBENCH_API_BASE_URL);

const nextConfig: NextConfig = {
  devIndicators: false,
  env: { NEXT_PUBLIC_RAGBENCH_API_BASE_URL: apiOrigin },
  /* config options here */
  experimental: {
    agentFeedback: true,
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
