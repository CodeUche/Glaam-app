"use client";

import Link from "next/link";
import { Sparkles, Instagram, Twitter, Facebook, Mail } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-neutral-100 bg-white">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-12 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="lg:col-span-1">
            <Link href="/" className="mb-4 flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-rose-500" />
              <span className="font-display text-xl font-bold text-neutral-900">
                Glam<span className="text-rose-500">Connect</span>
              </span>
            </Link>
            <p className="mb-6 text-sm leading-relaxed text-neutral-500">
              Connecting you with the best makeup artists in your area. Beauty
              made accessible, professional, and personal.
            </p>
            <div className="flex gap-3">
              {[
                { icon: Instagram, href: "#" },
                { icon: Twitter, href: "#" },
                { icon: Facebook, href: "#" },
                { icon: Mail, href: "#" },
              ].map(({ icon: Icon, href }, i) => (
                <a
                  key={i}
                  href={href}
                  className="flex h-9 w-9 items-center justify-center rounded-lg bg-neutral-100 text-neutral-500 transition-all hover:bg-rose-50 hover:text-rose-500"
                >
                  <Icon className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>

          {/* For Clients */}
          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-neutral-900">
              For Clients
            </h3>
            <ul className="space-y-3">
              {[
                { label: "Find Artists", href: "/artists" },
                { label: "How It Works", href: "/#how-it-works" },
                { label: "Pricing", href: "/pricing" },
                { label: "Reviews", href: "/reviews" },
              ].map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-neutral-500 transition-colors hover:text-rose-500"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* For Artists */}
          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-neutral-900">
              For Artists
            </h3>
            <ul className="space-y-3">
              {[
                { label: "Join as Artist", href: "/register" },
                { label: "Artist Dashboard", href: "/dashboard" },
                { label: "Resources", href: "/resources" },
                { label: "Success Stories", href: "/stories" },
              ].map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-neutral-500 transition-colors hover:text-rose-500"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-neutral-900">
              Company
            </h3>
            <ul className="space-y-3">
              {[
                { label: "About Us", href: "/about" },
                { label: "Contact", href: "/contact" },
                { label: "Privacy Policy", href: "/privacy" },
                { label: "Terms of Service", href: "/terms" },
              ].map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-neutral-500 transition-colors hover:text-rose-500"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-12 border-t border-neutral-100 pt-8">
          <p className="text-center text-sm text-neutral-400">
            &copy; {new Date().getFullYear()} GlamConnect. All rights reserved.
            Made with love for beauty professionals and their clients.
          </p>
        </div>
      </div>
    </footer>
  );
}
