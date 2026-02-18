"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  Search,
  Calendar,
  Star,
  Sparkles,
  MapPin,
  ArrowRight,
  Heart,
  Shield,
  Clock,
} from "lucide-react";
import api from "@/lib/api";
import type { ArtistProfile, PaginatedResponse } from "@/types";
import ArtistCard from "@/components/artists/ArtistCard";
import Button from "@/components/ui/Button";

export default function HomePage() {
  const { data: featuredArtists } = useQuery({
    queryKey: ["featured-artists"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<ArtistProfile>>(
        "/artists/",
        {
          params: { ordering: "-average_rating", page_size: 6 },
        }
      );
      return data.results;
    },
  });

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-glam pb-20 pt-32">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -right-40 -top-40 h-96 w-96 rounded-full bg-rose-200/30 blur-3xl" />
          <div className="absolute -left-20 top-1/2 h-72 w-72 rounded-full bg-blush-200/30 blur-3xl" />
          <div className="absolute bottom-0 right-1/4 h-60 w-60 rounded-full bg-glam-200/20 blur-3xl" />
        </div>

        <div className="glam-section relative z-10">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-rose-200 bg-white/80 px-4 py-2 text-sm font-medium text-rose-600 backdrop-blur-sm">
              <Sparkles className="h-4 w-4" />
              Your beauty, our expertise
            </div>

            <h1 className="mb-6 font-display text-5xl font-bold leading-tight tracking-tight text-neutral-900 sm:text-6xl lg:text-7xl">
              Find Your Perfect{" "}
              <span className="glam-gradient-text">Makeup Artist</span>
            </h1>

            <p className="mb-10 text-lg leading-relaxed text-neutral-600 sm:text-xl">
              Connect with talented, verified makeup artists in your area.
              Whether it&apos;s your wedding day, a photoshoot, or a night out
              &mdash; we&apos;ve got you covered.
            </p>

            <div className="mx-auto flex max-w-2xl flex-col gap-3 rounded-2xl border border-neutral-200 bg-white p-3 shadow-lg sm:flex-row">
              <div className="relative flex-1">
                <MapPin className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-neutral-400" />
                <input
                  type="text"
                  placeholder="Enter your location..."
                  className="w-full rounded-xl bg-neutral-50 py-3 pl-10 pr-4 text-sm outline-none transition-colors focus:bg-white focus:ring-2 focus:ring-rose-100"
                />
              </div>
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-neutral-400" />
                <input
                  type="text"
                  placeholder="Bridal, editorial, everyday..."
                  className="w-full rounded-xl bg-neutral-50 py-3 pl-10 pr-4 text-sm outline-none transition-colors focus:bg-white focus:ring-2 focus:ring-rose-100"
                />
              </div>
              <Link href="/artists">
                <Button variant="primary" size="lg">
                  <Search className="mr-2 h-4 w-4" />
                  Search
                </Button>
              </Link>
            </div>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-sm text-neutral-500">
              <span className="flex items-center gap-1">
                <Star className="h-4 w-4 text-glam-500" />
                500+ Verified Artists
              </span>
              <span className="flex items-center gap-1">
                <Heart className="h-4 w-4 text-rose-400" />
                10,000+ Happy Clients
              </span>
              <span className="flex items-center gap-1">
                <Shield className="h-4 w-4 text-emerald-500" />
                Satisfaction Guaranteed
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24">
        <div className="glam-section">
          <div className="mb-16 text-center">
            <h2 className="mb-4 font-display text-3xl font-bold text-neutral-900 sm:text-4xl">
              How It Works
            </h2>
            <p className="mx-auto max-w-2xl text-lg text-neutral-500">
              Getting your perfect look is just a few steps away
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3">
            {[
              {
                icon: Search,
                step: "01",
                title: "Discover Artists",
                description:
                  "Browse through our curated selection of professional makeup artists. Filter by specialty, location, price, and ratings.",
              },
              {
                icon: Calendar,
                step: "02",
                title: "Book a Session",
                description:
                  "Pick your services, choose a date and time, and book your appointment in minutes. Instant confirmation.",
              },
              {
                icon: Sparkles,
                step: "03",
                title: "Look Amazing",
                description:
                  "Your artist arrives prepared and ready. Sit back, relax, and get the stunning look you deserve.",
              },
            ].map((item) => (
              <div
                key={item.step}
                className="group relative rounded-2xl border border-neutral-100 bg-white p-8 text-center transition-all duration-300 hover:border-rose-100 hover:shadow-glam"
              >
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-gradient-rose px-3 py-1 text-xs font-bold text-white">
                  Step {item.step}
                </div>
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-rose-50 text-rose-500 transition-colors group-hover:bg-rose-100">
                  <item.icon className="h-7 w-7" />
                </div>
                <h3 className="mb-3 text-xl font-semibold text-neutral-900">
                  {item.title}
                </h3>
                <p className="leading-relaxed text-neutral-500">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Artists */}
      <section className="bg-white py-24">
        <div className="glam-section">
          <div className="mb-12 flex items-end justify-between">
            <div>
              <h2 className="mb-4 font-display text-3xl font-bold text-neutral-900 sm:text-4xl">
                Top Rated Artists
              </h2>
              <p className="text-lg text-neutral-500">
                Discover the most loved makeup professionals in your area
              </p>
            </div>
            <Link
              href="/artists"
              className="hidden items-center gap-2 text-sm font-semibold text-rose-600 transition-colors hover:text-rose-700 sm:flex"
            >
              View All Artists
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {featuredArtists?.map((artist) => (
              <ArtistCard key={artist.id} artist={artist} />
            ))}

            {!featuredArtists &&
              Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-80 animate-pulse rounded-2xl bg-neutral-100"
                />
              ))}
          </div>

          <div className="mt-8 text-center sm:hidden">
            <Link href="/artists">
              <Button variant="secondary">View All Artists</Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="bg-gradient-glam py-24">
        <div className="glam-section">
          <div className="mb-16 text-center">
            <h2 className="mb-4 font-display text-3xl font-bold text-neutral-900 sm:text-4xl">
              Why Choose GlamConnect
            </h2>
            <p className="mx-auto max-w-2xl text-lg text-neutral-500">
              We&apos;re redefining how you connect with beauty professionals
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                icon: Shield,
                title: "Verified Artists",
                description:
                  "Every artist is professionally vetted and verified",
              },
              {
                icon: Clock,
                title: "Instant Booking",
                description: "Book and confirm appointments in minutes",
              },
              {
                icon: Star,
                title: "Honest Reviews",
                description: "Real reviews from real clients you can trust",
              },
              {
                icon: Heart,
                title: "Satisfaction Guarantee",
                description:
                  "Not happy? We will make it right, guaranteed",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="rounded-2xl bg-white/80 p-6 backdrop-blur-sm transition-all duration-300 hover:bg-white hover:shadow-glam"
              >
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-rose-50 text-rose-500">
                  <feature.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 font-semibold text-neutral-900">
                  {feature.title}
                </h3>
                <p className="text-sm leading-relaxed text-neutral-500">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="glam-section">
          <div className="overflow-hidden rounded-3xl bg-gradient-rose p-12 text-center text-white sm:p-16">
            <h2 className="mb-4 font-display text-3xl font-bold sm:text-4xl">
              Ready to Shine?
            </h2>
            <p className="mx-auto mb-8 max-w-xl text-lg text-rose-100">
              Join thousands of clients who have found their perfect makeup
              artist through GlamConnect.
            </p>
            <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Link href="/register">
                <Button
                  variant="secondary"
                  size="lg"
                  className="border-white bg-white text-rose-600 hover:bg-rose-50"
                >
                  Get Started Free
                </Button>
              </Link>
              <Link href="/artists">
                <Button
                  variant="ghost"
                  size="lg"
                  className="border-2 border-white/30 text-white hover:bg-white/10"
                >
                  Browse Artists
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
