import { defineConfig } from 'vite';
export default defineConfig({ build: { outDir: '../src/chassis/portal/static', emptyOutDir: true, sourcemap: false },
  esbuild: { jsx: 'automatic' } });
