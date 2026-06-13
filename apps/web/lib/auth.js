const TOKEN_KEY = "personal-ai-agent-workspace-token";


export function getToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(TOKEN_KEY);
}


export function setToken(token) {
  if (typeof window === "undefined" || !token) {
    return;
  }

  window.localStorage.setItem(TOKEN_KEY, token);
}


export function clearToken() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(TOKEN_KEY);
}


export function isAuthenticated() {
  return Boolean(getToken());
}
