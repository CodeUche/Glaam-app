"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Star,
  MapPin,
  Clock,
  CheckCircle,
  Instagram,
  Globe,
  ChevronLeft,
  ChevronRight,
  Calendar,
  DollarSign,
  Award,
  Users,
} from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import type { ArtistProfile, Review, PaginatedResponse } from "@/types";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Modal from "@/components/ui/Modal";
import BookingForm from "@/components/bookings/BookingForm";
import ReviewCard from "@/components/reviews/ReviewCard";
import ReviewForm from "@/components/reviews/ReviewForm";
import { useAuthStore } from "@/lib/auth";

export default function ArtistDetailPage() {
  const params = useParams();
  const artistId = params.id as string;
  const { user, isAuthenticated } = useAuthStore();
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState<number | null>(
    null
  );

  const { data: artist, isLoading } = useQuery({
    queryKey: ["artist", artistId],
    queryFn: async () => {
      const { data } = await api.get<ArtistProfile>(`/artists/${artistId}/`);
      return data;
    },
  });

  const { data: reviews } = useQuery({
    queryKey: ["artist-reviews", artistId],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Review>>(
        `/artists/${artistId}/reviews/`
      );
      return data;
    },
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-neutral-50 py-8">
        <div className="mx-auto max-w-5xl px-4">
          <div className="animate-pulse space-y-6">
            <div className="h-8 w-48 rounded bg-neutral-200" />
            <div className="h-96 rounded-2xl bg-neutral-200" />
            <div className="h-32 rounded-2xl bg-neutral-200" />
          </div>
        </div>
      </div>
    );
  }

  if (!artist) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-neutral-900">
            Artist not found
          </h2>
          <Link href="/artists" className="mt-4 text-rose-600 hover:underline">
            Back to artists
          </Link>
        </div>
      </div>
    );
  }

  const { user: artistUser, services, portfolio_images } = artist;

  return (
    <div className="min-h-screen bg-neutral-50 py-8">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        {/* Back link */}
        <Link
          href="/artists"
          className="mb-6 inline-flex items-center gap-1 text-sm text-neutral-500 hover:text-neutral-700"
        >
          <ChevronLeft className="h-4 w-4" />
          Back to artists
        </Link>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Profile Header */}
            <Card className="mb-6">
              <div className="flex flex-col gap-6 sm:flex-row">
                <div className="flex h-28 w-28 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-400 to-blush-500 text-4xl font-bold text-white">
                  {artistUser.avatar ? (
                    <img
                      src={artistUser.avatar}
                      alt={artistUser.full_name}
                      className="h-full w-full rounded-2xl object-cover"
                    />
                  ) : (
                    `${artistUser.first_name.charAt(0)}${artistUser.last_name.charAt(0)}`
                  )}
                </div>

                <div className="flex-1">
                  <div className="mb-2 flex items-center gap-2">
                    <h1 className="font-display text-2xl font-bold text-neutral-900">
                      {artistUser.full_name}
                    </h1>
                    {artist.verified_at && (
                      <CheckCircle className="h-5 w-5 text-emerald-500" />
                    )}
                  </div>

                  <div className="mb-3 flex flex-wrap items-center gap-4 text-sm text-neutral-500">
                    {artistUser.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        {artistUser.location}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {artist.experience_years} years experience
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="h-4 w-4" />
                      {artist.total_bookings} bookings
                    </span>
                  </div>

                  <div className="mb-4 flex items-center gap-3">
                    <div className="flex items-center gap-1">
                      <Star className="h-5 w-5 fill-glam-500 text-glam-500" />
                      <span className="text-lg font-bold text-neutral-900">
                        {artist.average_rating.toFixed(1)}
                      </span>
                      <span className="text-sm text-neutral-400">
                        ({artist.total_reviews} reviews)
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {artist.specialties.map((s) => (
                      <Badge key={s} variant="rose">
                        {s}
                      </Badge>
                    ))}
                  </div>

                  <div className="mt-4 flex gap-3">
                    {artist.instagram_handle && (
                      <a
                        href={`https://instagram.com/${artist.instagram_handle}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-sm text-neutral-500 hover:text-rose-500"
                      >
                        <Instagram className="h-4 w-4" />@
                        {artist.instagram_handle}
                      </a>
                    )}
                    {artist.website && (
                      <a
                        href={artist.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-sm text-neutral-500 hover:text-rose-500"
                      >
                        <Globe className="h-4 w-4" />
                        Website
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </Card>

            {/* Bio */}
            <Card className="mb-6">
              <h2 className="mb-3 font-display text-xl font-semibold text-neutral-900">
                About
              </h2>
              <p className="leading-relaxed text-neutral-600">{artist.bio}</p>
            </Card>

            {/* Portfolio Gallery */}
            {portfolio_images.length > 0 && (
              <Card className="mb-6" padding="sm">
                <h2 className="mb-4 px-2 pt-2 font-display text-xl font-semibold text-neutral-900">
                  Portfolio
                </h2>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                  {portfolio_images.map((img, index) => (
                    <button
                      key={img.id}
                      onClick={() => setSelectedImageIndex(index)}
                      className="group relative aspect-square overflow-hidden rounded-xl"
                    >
                      <img
                        src={img.image_url}
                        alt={img.caption || "Portfolio image"}
                        className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                      />
                      <div className="absolute inset-0 bg-black/0 transition-all duration-300 group-hover:bg-black/20" />
                    </button>
                  ))}
                </div>
              </Card>
            )}

            {/* Services */}
            <Card className="mb-6">
              <h2 className="mb-4 font-display text-xl font-semibold text-neutral-900">
                Services
              </h2>
              <div className="space-y-3">
                {services.map((service) => (
                  <div
                    key={service.id}
                    className="flex items-center justify-between rounded-xl border border-neutral-100 p-4 transition-colors hover:bg-neutral-50"
                  >
                    <div>
                      <h3 className="font-medium text-neutral-900">
                        {service.name}
                      </h3>
                      <p className="mt-0.5 text-sm text-neutral-500">
                        {service.description}
                      </p>
                      <div className="mt-2 flex items-center gap-3 text-xs text-neutral-400">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {service.duration_minutes} min
                        </span>
                        <Badge variant="neutral" size="sm">
                          {service.category}
                        </Badge>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-neutral-900">
                        ${service.price}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Reviews */}
            <Card>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-display text-xl font-semibold text-neutral-900">
                  Reviews ({artist.total_reviews})
                </h2>
                {isAuthenticated && user?.role === "client" && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setShowReviewModal(true)}
                  >
                    Write a Review
                  </Button>
                )}
              </div>

              {reviews && reviews.results.length > 0 ? (
                <div className="space-y-4">
                  {reviews.results.map((review) => (
                    <ReviewCard key={review.id} review={review} />
                  ))}
                </div>
              ) : (
                <p className="py-8 text-center text-sm text-neutral-400">
                  No reviews yet. Be the first to review!
                </p>
              )}
            </Card>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-24 space-y-6">
              {/* Booking CTA */}
              <Card>
                <div className="mb-4 text-center">
                  <p className="text-sm text-neutral-500">Starting from</p>
                  <p className="text-3xl font-bold text-neutral-900">
                    ${artist.hourly_rate}
                  </p>
                  <p className="text-sm text-neutral-400">per session</p>
                </div>

                <div className="mb-4 space-y-2 rounded-xl bg-neutral-50 p-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-neutral-500">Availability</span>
                    <Badge
                      variant={artist.is_available ? "success" : "warning"}
                      size="sm"
                      dot
                    >
                      {artist.is_available ? "Available" : "Busy"}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-neutral-500">Travel radius</span>
                    <span className="font-medium text-neutral-700">
                      {artist.travel_radius_km} km
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-neutral-500">Response time</span>
                    <span className="font-medium text-neutral-700">
                      ~2 hours
                    </span>
                  </div>
                </div>

                <Button
                  variant="primary"
                  size="lg"
                  className="w-full"
                  onClick={() => setShowBookingModal(true)}
                  disabled={!artist.is_available}
                >
                  <Calendar className="mr-2 h-4 w-4" />
                  Book Now
                </Button>

                {!isAuthenticated && (
                  <p className="mt-3 text-center text-xs text-neutral-400">
                    <Link
                      href="/login"
                      className="text-rose-500 hover:underline"
                    >
                      Sign in
                    </Link>{" "}
                    to book this artist
                  </p>
                )}
              </Card>

              {/* Stats */}
              <Card>
                <h3 className="mb-4 font-semibold text-neutral-900">
                  Quick Stats
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    {
                      icon: Star,
                      label: "Rating",
                      value: artist.average_rating.toFixed(1),
                      color: "text-glam-500",
                    },
                    {
                      icon: Users,
                      label: "Bookings",
                      value: artist.total_bookings,
                      color: "text-blue-500",
                    },
                    {
                      icon: Award,
                      label: "Experience",
                      value: `${artist.experience_years}yr`,
                      color: "text-emerald-500",
                    },
                    {
                      icon: DollarSign,
                      label: "Services",
                      value: services.length,
                      color: "text-rose-500",
                    },
                  ].map((stat) => (
                    <div
                      key={stat.label}
                      className="rounded-xl bg-neutral-50 p-3 text-center"
                    >
                      <stat.icon
                        className={`mx-auto mb-1 h-5 w-5 ${stat.color}`}
                      />
                      <p className="text-lg font-bold text-neutral-900">
                        {stat.value}
                      </p>
                      <p className="text-xs text-neutral-400">{stat.label}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>

      {/* Image Lightbox */}
      {selectedImageIndex !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4">
          <button
            onClick={() => setSelectedImageIndex(null)}
            className="absolute right-4 top-4 text-white/70 hover:text-white"
          >
            <span className="text-3xl">&times;</span>
          </button>

          <button
            onClick={() =>
              setSelectedImageIndex(
                selectedImageIndex > 0
                  ? selectedImageIndex - 1
                  : portfolio_images.length - 1
              )
            }
            className="absolute left-4 rounded-full bg-white/10 p-2 text-white/70 hover:bg-white/20 hover:text-white"
          >
            <ChevronLeft className="h-6 w-6" />
          </button>

          <img
            src={portfolio_images[selectedImageIndex].image_url}
            alt={
              portfolio_images[selectedImageIndex].caption || "Portfolio image"
            }
            className="max-h-[85vh] max-w-[85vw] rounded-lg object-contain"
          />

          <button
            onClick={() =>
              setSelectedImageIndex(
                selectedImageIndex < portfolio_images.length - 1
                  ? selectedImageIndex + 1
                  : 0
              )
            }
            className="absolute right-4 rounded-full bg-white/10 p-2 text-white/70 hover:bg-white/20 hover:text-white"
          >
            <ChevronRight className="h-6 w-6" />
          </button>

          {portfolio_images[selectedImageIndex].caption && (
            <p className="absolute bottom-4 text-center text-sm text-white/70">
              {portfolio_images[selectedImageIndex].caption}
            </p>
          )}
        </div>
      )}

      {/* Booking Modal */}
      <Modal
        isOpen={showBookingModal}
        onClose={() => setShowBookingModal(false)}
        title="Book Appointment"
        size="lg"
      >
        <BookingForm
          artist={artist}
          onSuccess={() => setShowBookingModal(false)}
        />
      </Modal>

      {/* Review Modal */}
      <Modal
        isOpen={showReviewModal}
        onClose={() => setShowReviewModal(false)}
        title="Write a Review"
      >
        <ReviewForm
          artistId={artist.id}
          onSuccess={() => setShowReviewModal(false)}
        />
      </Modal>
    </div>
  );
}
