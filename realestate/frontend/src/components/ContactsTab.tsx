import { useCallback, useEffect, useState } from "react";
import { Plus, Search } from "lucide-react";
import { api } from "../api/client";
import type { Contact } from "../api/client";
import { ContactCard } from "./ContactCard";
import { ContactForm } from "./ContactForm";

export function ContactsTab() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [editing, setEditing] = useState<Contact | null | "new">(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const data = await api.getContacts({
      status: statusFilter || undefined,
      type: typeFilter || undefined,
      search: search || undefined,
    });
    setContacts(data);
    setLoading(false);
  }, [statusFilter, typeFilter, search]);

  useEffect(() => {
    const t = setTimeout(load, 200);
    return () => clearTimeout(t);
  }, [load]);

  async function handleSave(data: Partial<Contact>) {
    if (editing && editing !== "new") {
      await api.updateContact(editing.id, data);
    } else {
      await api.createContact(data);
    }
    setEditing(null);
    load();
  }

  async function handleDelete(contact: Contact) {
    if (!confirm(`Delete ${contact.name}?`)) return;
    await api.deleteContact(contact.id);
    load();
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[180px]">
          <Search className="w-3.5 h-3.5 text-stone-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search contacts..."
            className="input pl-8"
          />
        </div>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="input w-auto">
          <option value="">All types</option>
          <option value="buyer">Buyer</option>
          <option value="seller">Seller</option>
          <option value="lead">Lead</option>
          <option value="past_client">Past client</option>
          <option value="vendor">Vendor</option>
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="input w-auto">
          <option value="">All statuses</option>
          <option value="new">New</option>
          <option value="active">Active</option>
          <option value="nurturing">Nurturing</option>
          <option value="under_contract">Under contract</option>
          <option value="closed">Closed</option>
          <option value="lost">Lost</option>
        </select>
        <button
          onClick={() => setEditing("new")}
          className="flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 transition-colors font-medium"
        >
          <Plus className="w-3.5 h-3.5" />
          Add contact
        </button>
      </div>

      <div className="flex flex-col gap-2">
        {contacts.map((c) => (
          <ContactCard key={c.id} contact={c} onEdit={setEditing} onDelete={handleDelete} onChanged={load} />
        ))}
        {!loading && contacts.length === 0 && (
          <div className="text-center text-stone-500 text-sm py-8">No contacts match your filters yet.</div>
        )}
      </div>

      {editing && (
        <ContactForm
          contact={editing === "new" ? undefined : editing}
          onClose={() => setEditing(null)}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
