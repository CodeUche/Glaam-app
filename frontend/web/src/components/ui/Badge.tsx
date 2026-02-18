"use client";

import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?:
    | "default"
    | "success"
    | "warning"
    | "danger"
    | "info"
    | "rose"
    | "neutral";
  size?: "sm" | "md";
  className?: string;
  dot?: boolean;
}

const variantClasses: Record<string, string> = {
  default: "bg-neutral-100 text-neutral-600",
  success: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  warning: "bg-amber-50 text-amber-700 border border-amber-200",
  danger: "bg-red-50 text-red-700 border border-red-200",
  info: "bg-blue-50 text-blue-700 border border-blue-200",
  rose: "bg-rose-50 text-rose-700 border border-rose-200",
  neutral: "bg-neutral-50 text-neutral-600 border border-neutral-200",
};

const dotColors: Record<string, string> = {
  default: "bg-neutral-400",
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  danger: "bg-red-500",
  info: "bg-blue-500",
  rose: "bg-rose-500",
  neutral: "bg-neutral-400",
};

const sizeClasses: Record<string, string> = {
  sm: "px-2 py-0.5 text-xs",
  md: "px-3 py-1 text-xs",
};

export default function Badge({
  children,
  variant = "default",
  size = "md",
  className = "",
  dot = false,
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {dot && (
        <span
          className={`h-1.5 w-1.5 rounded-full ${dotColors[variant]}`}
        />
      )}
      {children}
    </span>
  );
}
