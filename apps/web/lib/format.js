export function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "-";
  }

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(parsed);
}


export function truncateText(value, maxLength = 100) {
  if (!value) {
    return "-";
  }

  if (value.length <= maxLength) {
    return value;
  }

  if (maxLength <= 3) {
    return `${value.slice(0, maxLength)}`;
  }

  return `${value.slice(0, maxLength - 3)}...`;
}


export function maskSensitiveReference(value) {
  if (!value) {
    return "-";
  }

  const lowerValue = value.toLowerCase();
  const looksSensitive =
    lowerValue.includes("token") ||
    lowerValue.includes("secret") ||
    lowerValue.includes("api_key") ||
    lowerValue.includes("authorization") ||
    lowerValue.includes("password") ||
    value.startsWith("http://") ||
    value.startsWith("https://");

  if (looksSensitive) {
    return "[masked reference]";
  }

  return value;
}
