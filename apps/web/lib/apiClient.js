import { clearToken, getToken } from "./auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
const API_BASE_URL_ERROR = "Frontend API configuration missing. Set NEXT_PUBLIC_API_BASE_URL.";
let currentUserCache = null;
let currentUserRequest = null;
let currentUserToken = null;

function clearCurrentUserCache() {
  currentUserCache = null;
  currentUserRequest = null;
  currentUserToken = null;
}

function buildUrl(pathname, query) {
  if (!API_BASE_URL) {
    throw new Error(API_BASE_URL_ERROR);
  }

  const url = `${API_BASE_URL.replace(/\/$/, "")}${pathname.startsWith("/") ? pathname : `/${pathname}`}`;

  if (!query || typeof query !== "object") {
    return url;
  }

  const searchParams = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    searchParams.set(key, String(value));
  });

  const queryString = searchParams.toString();
  return queryString ? `${url}?${queryString}` : url;
}


function handleUnauthorized() {
  clearCurrentUserCache();

  if (typeof window === "undefined") {
    return;
  }

  clearToken();
  if (window.location.pathname !== "/login") {
    const next = `${window.location.pathname}${window.location.search}`;
    window.location.assign(`/login?next=${encodeURIComponent(next || "/dashboard")}`);
  }
}


async function parseResponse(response, options = {}) {
  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await response.json() : await response.text();

  if (response.status === 401 && options.includeAuth !== false) {
    handleUnauthorized();
  }

  if (!response.ok) {
    const message =
      isJson && payload && typeof payload === "object" && "detail" in payload
        ? payload.detail
        : typeof payload === "string" && payload
          ? payload
          : "Request failed.";
    throw new Error(message);
  }

  return payload;
}


async function request(method, pathname, body, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  const includeAuth = options.includeAuth !== false;
  const token = includeAuth ? getToken() : null;
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(buildUrl(pathname, options.query), {
    method,
    headers,
    cache: "no-store",
    body: body === undefined ? undefined : JSON.stringify(body)
  });

  return parseResponse(response, { includeAuth });
}


export function get(pathname, options) {
  return request("GET", pathname, undefined, options);
}

export async function getCurrentUser(options = {}) {
  const token = getToken();

  if (!token) {
    clearCurrentUserCache();
    throw new Error("Missing authentication token.");
  }

  if (!options.force && currentUserCache && currentUserToken === token) {
    return currentUserCache;
  }

  if (!options.force && currentUserRequest && currentUserToken === token) {
    return currentUserRequest;
  }

  currentUserToken = token;
  currentUserRequest = get("/auth/me")
    .then((payload) => {
      currentUserCache = payload;
      return payload;
    })
    .catch((error) => {
      clearCurrentUserCache();
      throw error;
    })
    .finally(() => {
      currentUserRequest = null;
    });

  return currentUserRequest;
}


function ensureIdentifier(id, resourceName) {
  if (!id) {
    throw new Error(`Missing ${resourceName} identifier.`);
  }
}


export function getAgent(id, options) {
  ensureIdentifier(id, "agent");
  return get(`/agents/${id}`, options);
}

export function createAgent(payload, options) {
  return post("/agents", payload, options);
}

export function getSkills(options) {
  return get("/skills", options);
}

export function getModelProviders(options) {
  return get("/model-providers", options);
}


export function getTask(id, options) {
  ensureIdentifier(id, "task");
  return get(`/tasks/${id}`, options);
}


export function getApproval(id, options) {
  ensureIdentifier(id, "approval");
  return get(`/approvals/${id}`, options);
}


export function post(pathname, body, options) {
  return request("POST", pathname, body, options);
}
