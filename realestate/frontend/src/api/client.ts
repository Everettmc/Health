export interface ChecklistTemplate {
  id: string;
  name: string;
  description: string | null;
  icon: string;
  items: string[];
  is_default: number;
}

export interface ChecklistItem {
  text: string;
  done: boolean;
}

export interface Checklist {
  id: number;
  template_id: string | null;
  template_name: string;
  title: string;
  contact_id: number | null;
  event_date: string;
  items: ChecklistItem[];
  status: "active" | "completed";
  created_at: string;
  completed_at: string | null;
}

export type ContactType = "buyer" | "seller" | "lead" | "past_client" | "vendor";
export type ContactStatus = "new" | "active" | "nurturing" | "under_contract" | "closed" | "lost";

export interface Contact {
  id: number;
  name: string;
  phone: string | null;
  email: string | null;
  type: ContactType;
  status: ContactStatus;
  address: string | null;
  source: string | null;
  notes: string | null;
  follow_up_date: string | null;
  last_contact_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContactActivity {
  id: number;
  contact_id: number;
  activity_type: string;
  notes: string | null;
  created_at: string;
}

export interface NewsItem {
  id: number;
  title: string;
  link: string;
  source: string;
  summary: string;
  published_at: string;
  fetched_at: string;
}

export interface DailyBrief {
  date: string;
  todays_checklists: Checklist[];
  active_checklist_count: number;
  follow_ups_due_today: Contact[];
  follow_ups_overdue: Contact[];
  news: NewsItem[];
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Brief
  getBrief: () => request<DailyBrief>("/brief"),

  // Templates
  getTemplates: () => request<ChecklistTemplate[]>("/checklist-templates"),
  createTemplate: (data: { name: string; description?: string; icon?: string; items: string[] }) =>
    request<ChecklistTemplate>("/checklist-templates", { method: "POST", body: JSON.stringify(data) }),
  deleteTemplate: (id: string) => request<void>(`/checklist-templates/${id}`, { method: "DELETE" }),

  // Checklists
  getChecklists: (status?: string) =>
    request<Checklist[]>(`/checklists${status ? `?status=${status}` : ""}`),
  startChecklist: (data: { template_id?: string; title: string; event_date?: string; contact_id?: number; items?: string[] }) =>
    request<Checklist>("/checklists", { method: "POST", body: JSON.stringify(data) }),
  updateChecklist: (id: number, data: Partial<Pick<Checklist, "items" | "status" | "title">>) =>
    request<Checklist>(`/checklists/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteChecklist: (id: number) => request<void>(`/checklists/${id}`, { method: "DELETE" }),

  // Contacts
  getContacts: (params?: { status?: string; type?: string; search?: string }) => {
    const entries = Object.entries(params ?? {}).filter(([, v]) => v !== undefined) as [string, string][];
    const qs = new URLSearchParams(entries).toString();
    return request<Contact[]>(`/contacts${qs ? `?${qs}` : ""}`);
  },
  createContact: (data: Partial<Contact>) =>
    request<Contact>("/contacts", { method: "POST", body: JSON.stringify(data) }),
  updateContact: (id: number, data: Partial<Contact>) =>
    request<Contact>(`/contacts/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteContact: (id: number) => request<void>(`/contacts/${id}`, { method: "DELETE" }),
  getActivities: (contactId: number) => request<ContactActivity[]>(`/contacts/${contactId}/activities`),
  addActivity: (contactId: number, data: { activity_type: string; notes?: string }) =>
    request<ContactActivity>(`/contacts/${contactId}/activities`, { method: "POST", body: JSON.stringify(data) }),

  // News
  getNews: (limit = 30) => request<NewsItem[]>(`/news?limit=${limit}`),
  refreshNews: () => request<{ status: string; items_fetched: number }>("/news/refresh", { method: "POST" }),
};
