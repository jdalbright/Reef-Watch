import { defineConfig } from "vite";
export default defineConfig({
  build: { outDir: "../reefwatch/static", emptyOutDir: true },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8765",
      "/media": "http://127.0.0.1:8765",
    },
  },
});
