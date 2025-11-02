import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 5173,
  },
  plugins: [
    react(),
    mode === "development" && componentTagger(),
    // Custom plugin to handle SPA routing fallback for React Router
    {
      name: "spa-fallback",
      configureServer(server) {
        return () => {
          // Middleware to serve index.html for client-side routes
          server.middlewares.use((req, res, next) => {
            const url = req.url || "";
            
            // Skip API calls, static assets, and Vite's internal routes
            if (
              url.startsWith("/api") ||
              url.startsWith("/@") ||
              url.startsWith("/node_modules") ||
              url.includes(".") // Has file extension (e.g., .js, .css, .svg)
            ) {
              return next();
            }
            
            // For all other routes (like /upload), serve index.html
            // This allows React Router to handle the routing
            req.url = "/index.html";
            next();
          });
        };
      },
    },
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
