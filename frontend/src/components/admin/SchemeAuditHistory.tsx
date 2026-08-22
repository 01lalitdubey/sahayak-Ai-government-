"use client";

import {
  FilePlus,
  Send,
  Archive,
  RotateCcw,
  Edit,
  Languages,
  AlertCircle,
  Info,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useSchemeAuditHistory } from "@/hooks/use-schemes";
import type { AuditHistoryItem } from "@/types/scheme";
import { formatDate } from "@/lib/utils";

interface Props {
  schemeId: string;
}

const ACTION_CONFIG: Record<
  string,
  { label: string; icon: React.ElementType; iconClass: string; lineClass: string }
> = {
  SAVE_DRAFT: {
    label: "Saved as Draft",
    icon: FilePlus,
    iconClass: "bg-gray-100 text-gray-600",
    lineClass: "bg-gray-200",
  },
  PUBLISH_SCHEME: {
    label: "Published",
    icon: Send,
    iconClass: "bg-emerald-100 text-emerald-600",
    lineClass: "bg-emerald-200",
  },
  UNPUBLISH_SCHEME: {
    label: "Unpublished",
    icon: AlertCircle,
    iconClass: "bg-amber-100 text-amber-600",
    lineClass: "bg-amber-200",
  },
  UPDATE_SCHEME: {
    label: "Updated",
    icon: Edit,
    iconClass: "bg-blue-100 text-blue-600",
    lineClass: "bg-blue-200",
  },
  ARCHIVE_SCHEME: {
    label: "Archived",
    icon: Archive,
    iconClass: "bg-red-100 text-red-600",
    lineClass: "bg-red-200",
  },
  RESTORE_SCHEME: {
    label: "Restored",
    icon: RotateCcw,
    iconClass: "bg-violet-100 text-violet-600",
    lineClass: "bg-violet-200",
  },
  TRANSLATION_TRIGGERED: {
    label: "Translation Queued",
    icon: Languages,
    iconClass: "bg-indigo-100 text-indigo-600",
    lineClass: "bg-indigo-200",
  },
};

function getActionConfig(action: string) {
  return (
    ACTION_CONFIG[action] ?? {
      label: action.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()),
      icon: Info,
      iconClass: "bg-gray-100 text-gray-600",
      lineClass: "bg-gray-200",
    }
  );
}

function AuditEvent({ event, isLast }: { event: AuditHistoryItem; isLast: boolean }) {
  const cfg = getActionConfig(event.action);
  const Icon = cfg.icon;

  return (
    <li className="relative flex gap-4">
      {/* Vertical line */}
      {!isLast && (
        <div className={`absolute left-5 top-10 bottom-0 w-0.5 ${cfg.lineClass}`} />
      )}
      {/* Icon */}
      <div className={`relative z-10 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full ring-4 ring-white ${cfg.iconClass}`}>
        <Icon className="h-4 w-4" />
      </div>
      {/* Content */}
      <div className="flex-1 pb-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <p className="text-sm font-semibold text-gray-900">{cfg.label}</p>
          <time className="text-xs text-gray-400 tabular-nums">
            {formatDate(event.timestamp)}
          </time>
        </div>
        {event.admin_name && (
          <p className="text-xs text-gray-500 mt-0.5">
            by <span className="font-medium">{event.admin_name}</span>
            {event.admin_email && <span className="text-gray-400"> ({event.admin_email})</span>}
          </p>
        )}
        {event.details && Object.keys(event.details).length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {event.details.content_changed !== undefined && (
              <span
                className={`text-xs rounded-full px-2 py-0.5 font-medium ${
                  event.details.content_changed
                    ? "bg-amber-50 text-amber-700 ring-1 ring-amber-200"
                    : "bg-gray-50 text-gray-500 ring-1 ring-gray-200"
                }`}
              >
                {event.details.content_changed ? "Translatable content changed" : "Metadata only"}
              </span>
            )}
          </div>
        )}
        {event.result && event.result !== "success" && (
          <p className="mt-1 text-xs text-red-600 font-medium">Result: {event.result}</p>
        )}
      </div>
    </li>
  );
}

export function SchemeAuditHistory({ schemeId }: Props) {
  const { data, isLoading, isError } = useSchemeAuditHistory(schemeId);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex gap-4">
            <Skeleton className="h-10 w-10 rounded-full flex-shrink-0" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-3 w-32" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        Failed to load audit history.
      </div>
    );
  }

  if (data.events.length === 0) {
    return (
      <div className="rounded-lg bg-gray-50 p-6 text-center text-sm text-gray-500">
        No audit events recorded yet.
      </div>
    );
  }

  return (
    <div>
      <p className="text-xs text-gray-400 mb-4">{data.total} event{data.total !== 1 ? "s" : ""} recorded</p>
      <ul role="list" className="space-y-0">
        {data.events.map((event, i) => (
          <AuditEvent key={event.id} event={event} isLast={i === data.events.length - 1} />
        ))}
      </ul>
    </div>
  );
}
