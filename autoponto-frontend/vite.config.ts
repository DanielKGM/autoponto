import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, "..", "");
  if (!env.VITE_API_URL) {
    throw new Error("VITE_API_URL obrigatoria no .env da raiz.");
  }
  const base = env.VITE_BASE_PATH || "/";

  return {
    plugins: [react()],
    envDir: "..",
    base,
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: "http://localhost:8000",
          changeOrigin: true,
        },
        "/interscity_lh/catalog/autoponto/api": {
          target: "http://localhost:8000",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/interscity_lh\/catalog\/autoponto\/api/, "/api"),
        },
      },
    },
  };
});
