import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  serverExternalPackages: ["@sparticuz/chromium-min", "puppeteer-core"],
  env: {
    BUILD_TIME: new Date().toISOString(),
  },
};

export default nextConfig;
