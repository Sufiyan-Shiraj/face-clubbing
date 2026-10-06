import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './', // ensure relative paths work on static hosting (GitHub Pages, Cloudflare Pages, local folder)
  server: {
    port: 5173,
  },
});
