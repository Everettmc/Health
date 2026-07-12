import {
  Home,
  Users,
  ClipboardList,
  DoorOpen,
  KeyRound,
  ListChecks,
  type LucideIcon,
} from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  Home,
  Users,
  ClipboardList,
  DoorOpen,
  KeyRound,
  ListChecks,
};

export function TemplateIcon({ name, className }: { name: string; className?: string }) {
  const Icon = ICONS[name] || ListChecks;
  return <Icon className={className} />;
}
