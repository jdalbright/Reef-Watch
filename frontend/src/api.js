export async function request(path, method = "GET", body) {
  const response = await fetch(`/api/${path}`, {
    method,
    headers: { "Content-Type": "application/json", "X-Reef-Watch": "1" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.detail || "Request failed. Please try again.");
  return data;
}

export function when(timestamp) {
  return new Date(timestamp * 1000).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
