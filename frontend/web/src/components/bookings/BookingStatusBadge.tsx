"use client";

import type { BookingStatus } from "@/types";
import Badge from "@/components/ui/Badge";

interface BookingStatusBadgeProps {
  status: BookingStatus;
  size?: "sm" | "md";
}

const statusConfig: Record<
  BookingStatus,
  { label: string; variant: "success" | "warning" | "danger" | "info" | "neutral" | "rose" }
> = {
  pending: { label: "Pending", variant: "warning" },
  confirmed: { label: "Confirmed", variant: "info" },
  in_progress: { label: "In Progress", variant: "rose" },
  completed: { label: "Completed", variant: "success" },
  cancelled: { label: "Cancelled", variant: "danger" },
  declined: { label: "Declined", variant: "neutral" },
};

export default function BookingStatusBadge({
  status,
  size = "md",
}: BookingStatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} size={size} dot>
      {config.label}
    </Badge>
  );
}
