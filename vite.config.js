import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Relative asset paths in production builds, so the same build works whether GitHub Pages
// serves the Actions artifact (site root = Frontend/dist) or the repository branch
// (root index.html redirects to Frontend/dist/).
export default defineConfig(({ command }) => ({
  root: 'Frontend',
  base: command === 'build' ? './' : '/',
  resolve: {
    dedupe: ['react', 'react-dom', 'react-router-dom'],
  },
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
  },
}));
