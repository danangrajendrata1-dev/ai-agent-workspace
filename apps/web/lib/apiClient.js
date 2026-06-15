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


export function patch(pathname, body, options) {
  return request("PATCH", pathname, body, options);
}


export function put(pathname, body, options) {
  return request("PUT", pathname, body, options);
}


export function remove(pathname, options) {
  return request("DELETE", pathname, undefined, options);
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

export function previewAgentRouting(payload, options) {
  return post("/agents/routing-preview", payload, options);
}

export function getAgentActiveSkills(id, options) {
  ensureIdentifier(id, "agent");
  return get(`/agents/${id}/active-skills`, options);
}

export function createAgent(payload, options) {
  return post("/agents", payload, options);
}

export function getSkills(options) {
  return get("/skills", options);
}

export function getSkillLibrary(options) {
  return get("/skills/library", options);
}

export function getModelProviders(options) {
  return get("/model-providers", options);
}


export function getModelProviderSettings(options) {
  return get("/model-provider-settings", options);
}


export function updateModelProviderSettings(payload, options) {
  return patch("/model-provider-settings", payload, options);
}


export function getModelProviderKeyStatuses(options) {
  return get("/model-provider-keys", options);
}


export function saveModelProviderApiKey(provider, payload, options) {
  if (!provider) {
    throw new Error("Missing model provider identifier.");
  }

  return put(`/model-provider-keys/${provider}`, payload, options);
}


export function deleteModelProviderApiKey(provider, options) {
  if (!provider) {
    throw new Error("Missing model provider identifier.");
  }

  return remove(`/model-provider-keys/${provider}`, options);
}

export function getActivityLogs(options) {
  return get("/logs/activity", options);
}

export function getTasks(options) {
  return get("/tasks", options);
}

export function getPendingApprovals(options) {
  return get("/approvals/pending", options);
}


export function previewGithubSkillImport(payload, options) {
  return post("/github-imports/skills/preview", payload, options);
}


export function approveGithubSkillImport(importId, payload, options) {
  if (!importId) {
    throw new Error("Missing github import identifier.");
  }

  return post(`/github-imports/${importId}/approve-skill`, payload, options);
}

export function attachImportedSkillToAgent(agentId, skillId, options) {
  ensureIdentifier(agentId, "agent");
  ensureIdentifier(skillId, "skill");
  return post(`/agents/${agentId}/skills/imported/${skillId}`, undefined, options);
}

export function detachImportedSkillFromAgent(agentId, skillId, options) {
  ensureIdentifier(agentId, "agent");
  ensureIdentifier(skillId, "skill");
  return remove(`/agents/${agentId}/skills/imported/${skillId}`, options);
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
