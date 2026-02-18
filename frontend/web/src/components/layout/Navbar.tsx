"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Menu,
  X,
  User,
  LogOut,
  Calendar,
  LayoutDashboard,
  Bell,
  Sparkles,
  ChevronDown,
} from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import wsManager from "@/lib/websocket";
import type { Notification } from "@/types";
import Button from "@/components/ui/Button";

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  useEffect(() => {
    const unsubscribe = wsManager.onNotification((notification) => {
      setNotifications((prev) => [notification, ...prev].slice(0, 20));
    });
    return unsubscribe;
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        profileRef.current &&
        !profileRef.current.contains(e.target as Node)
      ) {
        setIsProfileMenuOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const navLinks = [
    { href: "/artists", label: "Find Artists" },
    ...(isAuthenticated
      ? [
          { href: "/bookings", label: "My Bookings" },
          ...(user?.role === "artist"
            ? [{ href: "/dashboard", label: "Dashboard" }]
            : []),
        ]
      : []),
  ];

  const isActive = (href: string) => pathname === href;

  return (
    <nav className="sticky top-0 z-40 border-b border-neutral-100 bg-white/90 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-rose-500" />
            <span className="font-display text-xl font-bold text-neutral-900">
              Glam<span className="text-rose-500">Connect</span>
            </span>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden items-center gap-8 md:flex">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`text-sm font-medium transition-colors ${
                  isActive(link.href)
                    ? "text-rose-600"
                    : "text-neutral-600 hover:text-neutral-900"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                {/* Notifications */}
                <div ref={notifRef} className="relative">
                  <button
                    onClick={() => setShowNotifications(!showNotifications)}
                    className="relative rounded-lg p-2 text-neutral-500 transition-colors hover:bg-neutral-100 hover:text-neutral-700"
                  >
                    <Bell className="h-5 w-5" />
                    {unreadCount > 0 && (
                      <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white">
                        {unreadCount}
                      </span>
                    )}
                  </button>

                  {showNotifications && (
                    <div className="absolute right-0 top-full mt-2 w-80 rounded-xl border border-neutral-100 bg-white shadow-lg">
                      <div className="border-b border-neutral-100 px-4 py-3">
                        <h3 className="text-sm font-semibold text-neutral-900">
                          Notifications
                        </h3>
                      </div>
                      <div className="max-h-80 overflow-y-auto">
                        {notifications.length === 0 ? (
                          <div className="p-4 text-center text-sm text-neutral-400">
                            No notifications yet
                          </div>
                        ) : (
                          notifications.map((notif) => (
                            <div
                              key={notif.id}
                              className={`border-b border-neutral-50 px-4 py-3 ${
                                !notif.is_read ? "bg-rose-50/50" : ""
                              }`}
                            >
                              <p className="text-sm font-medium text-neutral-900">
                                {notif.title}
                              </p>
                              <p className="text-xs text-neutral-500">
                                {notif.message}
                              </p>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Profile Menu */}
                <div ref={profileRef} className="relative">
                  <button
                    onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
                    className="flex items-center gap-2 rounded-lg px-2 py-1.5 transition-colors hover:bg-neutral-100"
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-rose-400 to-blush-500 text-sm font-semibold text-white">
                      {user?.first_name?.charAt(0) || "U"}
                    </div>
                    <span className="hidden text-sm font-medium text-neutral-700 md:block">
                      {user?.first_name}
                    </span>
                    <ChevronDown className="hidden h-4 w-4 text-neutral-400 md:block" />
                  </button>

                  {isProfileMenuOpen && (
                    <div className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-neutral-100 bg-white py-2 shadow-lg">
                      <div className="border-b border-neutral-100 px-4 pb-2 pt-1">
                        <p className="text-sm font-semibold text-neutral-900">
                          {user?.full_name}
                        </p>
                        <p className="text-xs text-neutral-500">
                          {user?.email}
                        </p>
                      </div>

                      <Link
                        href="/bookings"
                        className="flex items-center gap-3 px-4 py-2.5 text-sm text-neutral-600 transition-colors hover:bg-neutral-50"
                        onClick={() => setIsProfileMenuOpen(false)}
                      >
                        <Calendar className="h-4 w-4" />
                        My Bookings
                      </Link>

                      {user?.role === "artist" && (
                        <Link
                          href="/dashboard"
                          className="flex items-center gap-3 px-4 py-2.5 text-sm text-neutral-600 transition-colors hover:bg-neutral-50"
                          onClick={() => setIsProfileMenuOpen(false)}
                        >
                          <LayoutDashboard className="h-4 w-4" />
                          Dashboard
                        </Link>
                      )}

                      <Link
                        href="/profile"
                        className="flex items-center gap-3 px-4 py-2.5 text-sm text-neutral-600 transition-colors hover:bg-neutral-50"
                        onClick={() => setIsProfileMenuOpen(false)}
                      >
                        <User className="h-4 w-4" />
                        Profile
                      </Link>

                      <div className="border-t border-neutral-100 pt-1">
                        <button
                          onClick={() => {
                            setIsProfileMenuOpen(false);
                            logout();
                          }}
                          className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-red-600 transition-colors hover:bg-red-50"
                        >
                          <LogOut className="h-4 w-4" />
                          Sign Out
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center gap-3">
                <Link href="/login">
                  <Button variant="ghost" size="sm">
                    Sign In
                  </Button>
                </Link>
                <Link href="/register" className="hidden sm:block">
                  <Button variant="primary" size="sm">
                    Get Started
                  </Button>
                </Link>
              </div>
            )}

            {/* Mobile menu toggle */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="rounded-lg p-2 text-neutral-500 transition-colors hover:bg-neutral-100 md:hidden"
            >
              {isMobileMenuOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="border-t border-neutral-100 py-4 md:hidden">
            <div className="flex flex-col gap-2">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
                    isActive(link.href)
                      ? "bg-rose-50 text-rose-600"
                      : "text-neutral-600 hover:bg-neutral-50"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
              {!isAuthenticated && (
                <Link
                  href="/register"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="rounded-lg bg-rose-50 px-4 py-2.5 text-sm font-medium text-rose-600"
                >
                  Get Started
                </Link>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
