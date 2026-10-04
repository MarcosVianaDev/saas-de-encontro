import { defineConfig } from "vite";

export default defineConfig({
  server: {
    proxy: {
      "/api/": "http://backend:8000",
      "/admin/": "http://backend:8000",
      "/static/": "http://backend:8000",
    },
  },
});
