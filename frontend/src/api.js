const API_URL = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

export async function createTripPlan(payload) {
  const response = await fetch(`${API_URL}/plan/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "We could not build this trip plan. Please try again.");
  }
  return data;
}

