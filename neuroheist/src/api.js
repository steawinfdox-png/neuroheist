// Public service URL only. Never put API keys in VITE_ variables.
const configuredBase = (import.meta.env.VITE_API_BASE_URL || "https://neuroheist-backend.onrender.com").trim();
const parsedBase = new URL(configuredBase, window.location.origin);
if (!["http:", "https:"].includes(parsedBase.protocol)) {
  throw new Error("VITE_API_BASE_URL must use HTTP or HTTPS.");
}
if (import.meta.env.PROD && configuredBase.startsWith("http://")) {
  throw new Error("Production VITE_API_BASE_URL must use HTTPS.");
}
export const API_BASE_URL = parsedBase.href.replace(/\/+$/, "");
export function apiUrl(path) {
  return new URL(path, API_BASE_URL + "/").href;
}
