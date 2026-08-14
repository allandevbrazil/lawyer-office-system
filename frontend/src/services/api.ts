import axios from "axios";

import { environment } from "@/config/env";
import type { TokenResponse } from "@/types/auth";

let transientAccessToken: string | null = null;

const api = axios.create({
  baseURL: environment.apiBaseUrl,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  if (transientAccessToken) {
    config.headers.Authorization = `Bearer ${transientAccessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (
      error.response?.status !== 401 ||
      error.config?.url?.endsWith("/auth/refresh") ||
      error.config?._retry
    ) {
      return Promise.reject(error);
    }
    error.config._retry = true;
    try {
      const { data } = await api.post<TokenResponse>("/auth/refresh");
      transientAccessToken = data.access_token;
      error.config.headers.Authorization = `Bearer ${data.access_token}`;
      return api.request(error.config);
    } catch {
      transientAccessToken = null;
      return Promise.reject(error);
    }
  },
);

export const authApi = {
  setAccessToken(token: string | null): void {
    transientAccessToken = token;
  },

  async login(email: string, password: string): Promise<TokenResponse> {
    const body = new URLSearchParams({ username: email, password });
    const { data } = await api.post<TokenResponse>("/auth/token", body, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return data;
  },

  async refresh(): Promise<TokenResponse> {
    const { data } = await api.post<TokenResponse>("/auth/refresh");
    return data;
  },

  async logout(): Promise<void> {
    await api.post("/auth/logout");
    transientAccessToken = null;
  },

  async register(payload: Record<string, string>): Promise<TokenResponse["user"]> {
    const { data } = await api.post<TokenResponse["user"]>("/auth/register", payload);
    return data;
  },

  async forgotPassword(email: string): Promise<void> {
    await api.post("/auth/forgot-password", { email });
  },

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await api.post("/auth/reset-password", { token, new_password: newPassword });
  },

  async me(token: string): Promise<TokenResponse["user"]> {
    const { data } = await api.get<TokenResponse["user"]>("/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
};

export interface DashboardSummary {
  active_cases: number;
  pending_invoices: number;
  billing_total: string;
}

export interface CaseItem {
  id: string;
  firm_id: string;
  title: string;
  description: string | null;
  case_number: string | null;
  responsible_user_id: string | null;
  court: string | null;
  jurisdiction: string | null;
  case_type: string | null;
  status: string;
  priority: string;
  client_id: string;
  opened_at: string;
  closed_at: string | null;
}

export interface CaseCreateInput {
  client_id: string;
  title: string;
  description?: string;
  case_number?: string;
  court?: string;
  jurisdiction?: string;
  case_type?: string;
  priority?: string;
}

export interface CaseUpdateInput {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  responsible_user_id?: string;
}

export const dashboardApi = {
  async summary(token: string): Promise<DashboardSummary> {
    const { data } = await api.get<DashboardSummary>("/dashboard/summary", {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
};

export const casesApi = {
  async list(token: string, search?: string): Promise<CaseItem[]> {
    const { data } = await api.get<CaseItem[]>("/cases", {
      headers: { Authorization: `Bearer ${token}` },
      params: search ? { search } : undefined,
    });
    return data;
  },
  async create(token: string, payload: CaseCreateInput): Promise<CaseItem> {
    const { data } = await api.post<CaseItem>("/cases", payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async update(token: string, id: string, payload: CaseUpdateInput): Promise<CaseItem> {
    const { data } = await api.patch<CaseItem>(`/cases/${id}`, payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async remove(token: string, id: string): Promise<void> {
    await api.delete(`/cases/${id}`, { headers: { Authorization: `Bearer ${token}` } });
  },
};

export interface InvoiceItem {
  id: string;
  description: string;
  quantity: string;
  unit_price: string;
  amount: string;
}

export interface InvoiceItemView extends InvoiceItem {
  invoice_id?: string;
}

export interface Invoice {
  id: string;
  client_id: string;
  number: string;
  subtotal: string;
  discount: string;
  total: string;
  due_date: string;
  status: string;
  paid_at: string | null;
  items: InvoiceItem[];
}

export interface InvoiceCreateInput {
  client_id: string;
  case_id?: string;
  number: string;
  description?: string;
  discount?: string;
  due_date: string;
  items: Array<{ description: string; quantity: string; unit_price: string; service_id?: string }>;
}

export interface InvoiceStatusUpdateInput {
  status: string;
}

export interface ClientItem {
  id: string;
  firm_id: string;
  user_id: string | null;
  type: "PF" | "PJ";
  name: string;
  document_number: string | null;
  email: string | null;
  phone: string | null;
  notes: string | null;
  status: string;
}

export interface ClientCreateInput {
  type: "PF" | "PJ";
  name: string;
  document_number?: string;
  email?: string;
  phone?: string;
  notes?: string;
}

export interface ClientUpdateInput {
  name?: string;
  email?: string;
  phone?: string;
  notes?: string;
  status?: string;
}

export interface DocumentItem {
  id: string;
  client_id: string | null;
  case_id: string | null;
  file_name: string;
  mime_type: string;
  size_bytes: number;
  visibility: string;
  uploaded_at: string;
}

export interface DocumentUploadInput {
  file: File;
  client_id?: string;
  case_id?: string;
  visibility?: string;
}

export const invoicesApi = {
  async list(token: string): Promise<Invoice[]> {
    const { data } = await api.get<Invoice[]>("/invoices", {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async create(token: string, payload: InvoiceCreateInput): Promise<Invoice> {
    const { data } = await api.post<Invoice>("/invoices", payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async updateStatus(
    token: string,
    id: string,
    payload: InvoiceStatusUpdateInput,
  ): Promise<Invoice> {
    const { data } = await api.patch<Invoice>(`/invoices/${id}`, payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async remove(token: string, id: string): Promise<void> {
    await api.delete(`/invoices/${id}`, { headers: { Authorization: `Bearer ${token}` } });
  },
};

export const clientsApi = {
  async list(token: string, search?: string): Promise<ClientItem[]> {
    const { data } = await api.get<ClientItem[]>("/clients", {
      headers: { Authorization: `Bearer ${token}` },
      params: search ? { search } : undefined,
    });
    return data;
  },
  async create(token: string, payload: ClientCreateInput): Promise<ClientItem> {
    const { data } = await api.post<ClientItem>("/clients", payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async update(token: string, id: string, payload: ClientUpdateInput): Promise<ClientItem> {
    const { data } = await api.patch<ClientItem>(`/clients/${id}`, payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async remove(token: string, id: string): Promise<void> {
    await api.delete(`/clients/${id}`, { headers: { Authorization: `Bearer ${token}` } });
  },
};

export const documentsApi = {
  async list(token: string): Promise<DocumentItem[]> {
    const { data } = await api.get<DocumentItem[]>("/documents", {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async upload(token: string, payload: DocumentUploadInput): Promise<DocumentItem> {
    const body = new FormData();
    body.append("file", payload.file);
    if (payload.client_id) body.append("client_id", payload.client_id);
    if (payload.case_id) body.append("case_id", payload.case_id);
    if (payload.visibility) body.append("visibility", payload.visibility);
    const { data } = await api.post<DocumentItem>("/documents", body, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async download(token: string, id: string): Promise<Blob> {
    const { data } = await api.get(`/documents/${id}/download`, {
      headers: { Authorization: `Bearer ${token}` },
      responseType: "blob",
    });
    return data;
  },
  async remove(token: string, id: string): Promise<void> {
    await api.delete(`/documents/${id}`, { headers: { Authorization: `Bearer ${token}` } });
  },
};

export interface StaffItem {
  id: string;
  email: string;
  full_name: string;
  role: string;
  status: string;
  firm_id: string;
}

export interface StaffCreateInput {
  email: string;
  full_name: string;
  password: string;
  role?: string;
  phone?: string;
}
export interface StaffUpdateInput {
  email?: string;
  full_name?: string;
  password?: string;
  role?: string;
  status?: string;
  phone?: string;
}

export interface WikiItem {
  id: string;
  slug?: string;
  author_user_id?: string;
  title: string;
  category: string | null;
  content_markdown: string;
  status: string;
}

export interface WikiCreateInput {
  title: string;
  slug: string;
  content_markdown: string;
  category?: string;
  status?: string;
}
export interface WikiUpdateInput {
  title?: string;
  slug?: string;
  content_markdown?: string;
  category?: string;
  status?: string;
}

export const adminApi = {
  async staff(token: string): Promise<StaffItem[]> {
    const { data } = await api.get<StaffItem[]>("/staff", {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async createStaff(token: string, payload: StaffCreateInput): Promise<StaffItem> {
    const { data } = await api.post<StaffItem>("/staff", payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async updateStaff(token: string, id: string, payload: StaffUpdateInput): Promise<StaffItem> {
    const { data } = await api.patch<StaffItem>(`/staff/${id}`, payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async removeStaff(token: string, id: string): Promise<void> {
    await api.delete(`/staff/${id}`, { headers: { Authorization: `Bearer ${token}` } });
  },
  async wiki(token: string): Promise<WikiItem[]> {
    const { data } = await api.get<WikiItem[]>("/wiki/articles", {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async createWiki(token: string, payload: WikiCreateInput): Promise<WikiItem> {
    const { data } = await api.post<WikiItem>("/wiki/articles", payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async updateWiki(token: string, id: string, payload: WikiUpdateInput): Promise<WikiItem> {
    const { data } = await api.patch<WikiItem>(`/wiki/articles/${id}`, payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async removeWiki(token: string, id: string): Promise<void> {
    await api.delete(`/wiki/articles/${id}`, { headers: { Authorization: `Bearer ${token}` } });
  },
  async firmSettings(token: string): Promise<Record<string, unknown>> {
    const { data } = await api.get<Record<string, unknown>>("/settings/firm", {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
  async updateFirmSettings(
    token: string,
    payload: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    const { data } = await api.patch<Record<string, unknown>>("/settings/firm", payload, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
};

export default api;
