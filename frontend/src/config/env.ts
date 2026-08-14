const apiBaseUrl = (
  import.meta.env.VITE_LAWFIRM_API_URL?.trim() || import.meta.env.VITE_API_BASE_URL?.trim()
);
const appEnv = import.meta.env.VITE_APP_ENV?.trim() || "development";

if (!apiBaseUrl) {
  throw new Error(
    "VITE_LAWFIRM_API_URL não está configurada. Crie frontend/.env.local a partir de frontend/.env.example.",
  );
}

if (!["development", "production", "test"].includes(appEnv)) {
  throw new Error(`VITE_APP_ENV inválido: ${appEnv}`);
}

try {
  const parsedUrl = new URL(apiBaseUrl);
  if (!parsedUrl.protocol.startsWith("http")) {
    throw new Error("A URL da API deve usar http ou https.");
  }
} catch {
  throw new Error(`VITE_LAWFIRM_API_URL inválida: ${apiBaseUrl}`);
}

export const environment = {
  appEnv,
  apiBaseUrl: apiBaseUrl.replace(/\/$/, ""),
} as const;
