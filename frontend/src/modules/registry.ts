import {
  GraduationCap,
  LayoutDashboard,
  MessageCircle,
  MessagesSquare,
  Repeat,
  type LucideIcon,
} from "lucide-react";

/** Frontend side of a backend module: where it lives and how it appears in navigation. */
export interface ModuleNavEntry {
  key: string;
  path: string;
  label: string;
  icon: LucideIcon;
}

export const MODULE_NAV: ModuleNavEntry[] = [
  { key: "progress", path: "/", label: "Start", icon: LayoutDashboard },
  { key: "phrases", path: "/phrases", label: "Frazy", icon: MessageCircle },
  { key: "review", path: "/review", label: "Powtórki", icon: Repeat },
  { key: "conversation", path: "/conversation", label: "Rozmowa", icon: MessagesSquare },
  { key: "lessons", path: "/lessons", label: "Lekcje", icon: GraduationCap },
];
