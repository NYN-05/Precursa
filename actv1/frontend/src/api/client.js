import axios from "axios";

export const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api/v1";

const DEFAULT_USERNAME = import.meta.env.VITE_DEFAULT_USERNAME || "admin";
const DEFAULT_PASSWORD = import.meta.env.VITE_DEFAULT_PASSWORD || "admin123";
const TOKEN_STORAGE_KEY = "precursa_access_token";

export async function ensureAccessToken() {
  const cachedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  if (cachedToken) {
    return cachedToken;
  }

  const formData = new URLSearchParams();
  formData.set("username", DEFAULT_USERNAME);
  formData.set("password", DEFAULT_PASSWORD);

  try {
    const response = await axios.post(`${API_PREFIX}/auth/token`, formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    const token = response?.data?.access_token;
    if (token) {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
      return token;
    }
  } catch {
    // Keep endpoints usable in MVP mode where auth fallback is enabled.
  }

  return null;
}

export function authHeaders(token) {
  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}
