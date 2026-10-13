import { defineConfig } from 'vite'

// Preview live de la maquette web/ de BAE (rechargement à chaque sauvegarde)
export default defineConfig({
  root: 'web',
  server: { port: Number(process.env.PORT) || 5174, strictPort: true },
})
