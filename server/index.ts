// Static application - no server needed
// This file exists only to satisfy the current workflow
// In production, use `vite build` to generate static files

import { createServer } from 'vite';

const server = await createServer({
  configFile: './vite.config.ts'
});

await server.listen(5000);
console.log('Static development server running on http://localhost:5000');
