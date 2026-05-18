// In dev, VITE_API_URL is unset — Vite's proxy forwards /api/* to localhost:8000.
// In production (Vercel), set VITE_API_URL=https://your-backend.onrender.com
export const API_BASE = import.meta.env.VITE_API_URL ?? "";
