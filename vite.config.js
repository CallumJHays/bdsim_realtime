import { defineConfig } from 'vite';
import { createHtmlPlugin } from 'vite-plugin-html';

export default defineConfig({
  // …
  plugins: [
    createHtmlPlugin({
      inject: {
        data: {
          title: env === 'production' ? 'BDSim-Web' : `BDSim-Web [${env.toUpperCase()}]`,
        },
      },
    }),
    react({
      // Use React plugin in all *.jsx and *.tsx files
      include: '**/*.{jsx,tsx}',
    }),
  ],
});