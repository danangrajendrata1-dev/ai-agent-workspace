const SENSITIVE_KEY_PARTS = [
  "token",
  "password",
  "secret",
  "api_key",
  "apikey",
  "authorization",
  "credential",
  "database_url",
  "webhook_url",
  "webhook_url_reference",
  "secret_reference",
  "oauth",
  "access_token",
  "refresh_token"
];


function isSensitiveKey(key) {
  const normalizedKey = String(key || "").toLowerCase();
  return SENSITIVE_KEY_PARTS.some((part) => normalizedKey.includes(part));
}


function isSensitiveString(value) {
  const normalizedValue = String(value || "").toLowerCase();
  return (
    normalizedValue.startsWith("bearer ") ||
    normalizedValue.startsWith("sk-") ||
    SENSITIVE_KEY_PARTS.some((part) => normalizedValue.includes(part)) ||
    normalizedValue.startsWith("http://") ||
    normalizedValue.startsWith("https://")
  );
}


export function maskSensitiveValue(value) {
  if (value === null || value === undefined) {
    return value;
  }

  if (Array.isArray(value)) {
    return value.map((item) => maskSensitiveValue(item));
  }

  if (typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, nestedValue]) => [
        key,
        isSensitiveKey(key) ? "[masked]" : maskSensitiveValue(nestedValue)
      ])
    );
  }

  if (typeof value === "string") {
    return isSensitiveString(value) ? "[masked]" : value;
  }

  return value;
}


export function formatPayloadPreview(value) {
  if (!value) {
    return "-";
  }

  try {
    const maskedValue = maskSensitiveValue(value);
    return JSON.stringify(maskedValue, null, 2);
  } catch {
    return "[unavailable payload preview]";
  }
}
