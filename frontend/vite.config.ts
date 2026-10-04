import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api/": "http://backend:8000",
      "/admin/": "http://backend:8000",
      "/static/": "http://backend:8000",
    },
  },
});
