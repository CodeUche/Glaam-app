"use client";

import Link from "next/link";
import { Star, MapPin, Clock, CheckCircle } from "lucide-react";
import type { ArtistProfile } from "@/types";
import Badge from "@/components/ui/Badge";

interface ArtistCardProps {
  artist: ArtistProfile;
}

export default function ArtistCard({ artist }: ArtistCardProps) {
  const { user, specialties, hourly_rate, average_rating, total_reviews, is_available } =
    artist;

  return (
    <Link href={`/artists/${artist.id}`}>
      <div className="group overflow-hidden rounded-2xl border border-neutral-100 bg-white shadow-sm transition-all duration-300 hover:border-rose-100 hover:shadow-glam">
        {/* Image */}
        <div className="relative h-56 overflow-hidden bg-gradient-to-br from-rose-100 to-blush-100">
          {artist.portfolio_images?.[0] ? (
            <img
              src={artist.portfolio_images[0].image_url}
              alt={user.full_name}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-white/80 text-3xl font-bold text-rose-400">
                {user.first_name.charAt(0)}
                {user.last_name.charAt(0)}
              </div>
            </div>
          )}

          {/* Availability badge */}
          <div className="absolute right-3 top-3">
            <Badge
              variant={is_available ? "success" : "neutral"}
              size="sm"
              dot
            >
              {is_available ? "Available" : "Busy"}
            </Badge>
          </div>

          {/* Verified badge */}
          {artist.verified_at && (
            <div className="absolute left-3 top-3">
              <div className="flex items-center gap-1 rounded-full bg-white/90 px-2 py-1 text-xs font-medium text-emerald-600 backdrop-blur-sm">
                <CheckCircle className="h-3 w-3" />
                Verified
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-5">
          <div className="mb-3 flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-neutral-900 group-hover:text-rose-600">
                {user.full_name}
              </h3>
              {user.location && (
                <p className="mt-0.5 flex items-center gap-1 text-xs text-neutral-400">
                  <MapPin className="h-3 w-3" />
                  {user.location}
                </p>
              )}
            </div>
            <div className="text-right">
              <p className="text-lg font-bold text-neutral-900">
                ${hourly_rate}
              </p>
              <p className="text-xs text-neutral-400">per session</p>
            </div>
          </div>

          {/* Rating */}
          <div className="mb-3 flex items-center gap-2">
            <div className="flex items-center gap-1">
              <Star className="h-4 w-4 fill-glam-500 text-glam-500" />
              <span className="text-sm font-semibold text-neutral-900">
                {average_rating.toFixed(1)}
              </span>
            </div>
            <span className="text-xs text-neutral-400">
              ({total_reviews} review{total_reviews !== 1 ? "s" : ""})
            </span>
            <span className="text-xs text-neutral-300">|</span>
            <span className="flex items-center gap-1 text-xs text-neutral-400">
              <Clock className="h-3 w-3" />
              {artist.experience_years}yr exp
            </span>
          </div>

          {/* Specialties */}
          <div className="flex flex-wrap gap-1.5">
            {specialties.slice(0, 3).map((specialty) => (
              <Badge key={specialty} variant="rose" size="sm">
                {specialty}
              </Badge>
            ))}
            {specialties.length > 3 && (
              <Badge variant="neutral" size="sm">
                +{specialties.length - 3}
              </Badge>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
