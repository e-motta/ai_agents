import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const getBasePath = () => {
  // For docker-compose, use root path
  if (
    process.env.NODE_ENV === "development" ||
    process.env.DOCKER_COMPOSE === "true"
  ) {
    return "/";
  }
  // For k8s, use /frontend/ path
  return "/frontend/";
};

export default defineConfig({
  plugins: [react()],
  base: getBasePath(),
  build: {
    outDir: "dist",
    assetsDir: "assets",
    sourcemap: false,
  },
  server: {
    host: true,
    port: 3000,
    open: true,
  },
});
