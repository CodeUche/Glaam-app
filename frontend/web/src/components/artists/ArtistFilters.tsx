"use client";

import { useState } from "react";
import { Search, SlidersHorizontal, X, Star } from "lucide-react";
import type { ArtistFilters as ArtistFiltersType } from "@/types";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";

interface ArtistFiltersProps {
  filters: ArtistFiltersType;
  onFilterChange: (filters: ArtistFiltersType) => void;
  isOpen: boolean;
  onToggle: () => void;
}

const specialties = [
  "Bridal",
  "Editorial",
  "Special Occasion",
  "Everyday Glam",
  "SFX",
  "Theatrical",
  "Lessons",
  "Natural/No-Makeup Look",
  "Cut Crease",
  "Airbrush",
];

const priceRanges = [
  { label: "Under $50", min: 0, max: 50 },
  { label: "$50 - $100", min: 50, max: 100 },
  { label: "$100 - $200", min: 100, max: 200 },
  { label: "$200 - $500", min: 200, max: 500 },
  { label: "$500+", min: 500, max: undefined },
];

const sortOptions = [
  { label: "Top Rated", value: "-average_rating" },
  { label: "Most Reviews", value: "-total_reviews" },
  { label: "Price: Low to High", value: "hourly_rate" },
  { label: "Price: High to Low", value: "-hourly_rate" },
  { label: "Most Experience", value: "-experience_years" },
  { label: "Newest", value: "-created_at" },
];

export default function ArtistFilters({
  filters,
  onFilterChange,
  isOpen,
  onToggle,
}: ArtistFiltersProps) {
  const [localSearch, setLocalSearch] = useState(filters.search || "");

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange({ ...filters, search: localSearch, page: 1 });
  };

  const handleSpecialtyToggle = (specialty: string) => {
    const current = filters.specialty;
    const newSpecialty = current === specialty ? undefined : specialty;
    onFilterChange({ ...filters, specialty: newSpecialty, page: 1 });
  };

  const handlePriceRange = (min: number, max: number | undefined) => {
    onFilterChange({
      ...filters,
      min_price: min,
      max_price: max,
      page: 1,
    });
  };

  const handleRatingFilter = (rating: number) => {
    onFilterChange({
      ...filters,
      min_rating: filters.min_rating === rating ? undefined : rating,
      page: 1,
    });
  };

  const clearAllFilters = () => {
    setLocalSearch("");
    onFilterChange({ page: 1 });
  };

  const hasActiveFilters =
    filters.specialty ||
    filters.min_price ||
    filters.max_price ||
    filters.min_rating ||
    filters.search;

  return (
    <div>
      {/* Search Bar */}
      <form onSubmit={handleSearchSubmit} className="mb-4">
        <Input
          placeholder="Search artists by name, specialty..."
          icon={<Search className="h-4 w-4" />}
          value={localSearch}
          onChange={(e) => setLocalSearch(e.target.value)}
        />
      </form>

      {/* Filter Toggle (Mobile) */}
      <div className="mb-4 flex items-center justify-between lg:hidden">
        <button
          onClick={onToggle}
          className="flex items-center gap-2 rounded-xl border border-neutral-200 px-4 py-2.5 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-50"
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {hasActiveFilters && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-rose-500 text-xs text-white">
              !
            </span>
          )}
        </button>

        {/* Sort dropdown */}
        <select
          value={filters.ordering || ""}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              ordering: e.target.value || undefined,
              page: 1,
            })
          }
          className="rounded-xl border border-neutral-200 px-4 py-2.5 text-sm text-neutral-700 outline-none focus:border-rose-300 focus:ring-2 focus:ring-rose-100"
        >
          <option value="">Sort By</option>
          {sortOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Filter Panel */}
      <div
        className={`${
          isOpen ? "block" : "hidden"
        } space-y-6 rounded-2xl border border-neutral-100 bg-white p-6 shadow-sm lg:block`}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-neutral-900">Filters</h3>
          {hasActiveFilters && (
            <button
              onClick={clearAllFilters}
              className="flex items-center gap-1 text-xs font-medium text-rose-600 hover:text-rose-700"
            >
              <X className="h-3 w-3" />
              Clear all
            </button>
          )}
        </div>

        {/* Sort (Desktop) */}
        <div className="hidden lg:block">
          <label className="mb-2 block text-sm font-medium text-neutral-700">
            Sort By
          </label>
          <select
            value={filters.ordering || ""}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                ordering: e.target.value || undefined,
                page: 1,
              })
            }
            className="w-full rounded-xl border border-neutral-200 px-3 py-2.5 text-sm text-neutral-700 outline-none focus:border-rose-300 focus:ring-2 focus:ring-rose-100"
          >
            <option value="">Default</option>
            {sortOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Specialties */}
        <div>
          <h4 className="mb-3 text-sm font-medium text-neutral-700">
            Specialty
          </h4>
          <div className="flex flex-wrap gap-2">
            {specialties.map((specialty) => (
              <button
                key={specialty}
                onClick={() => handleSpecialtyToggle(specialty)}
                className={`rounded-full px-3 py-1.5 text-xs font-medium transition-all ${
                  filters.specialty === specialty
                    ? "bg-rose-500 text-white"
                    : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200"
                }`}
              >
                {specialty}
              </button>
            ))}
          </div>
        </div>

        {/* Price Range */}
        <div>
          <h4 className="mb-3 text-sm font-medium text-neutral-700">
            Price Range
          </h4>
          <div className="space-y-2">
            {priceRanges.map((range) => (
              <button
                key={range.label}
                onClick={() => handlePriceRange(range.min, range.max)}
                className={`block w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                  filters.min_price === range.min &&
                  filters.max_price === range.max
                    ? "bg-rose-50 font-medium text-rose-700"
                    : "text-neutral-600 hover:bg-neutral-50"
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>

        {/* Rating */}
        <div>
          <h4 className="mb-3 text-sm font-medium text-neutral-700">
            Minimum Rating
          </h4>
          <div className="space-y-2">
            {[4, 3, 2].map((rating) => (
              <button
                key={rating}
                onClick={() => handleRatingFilter(rating)}
                className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
                  filters.min_rating === rating
                    ? "bg-rose-50 font-medium text-rose-700"
                    : "text-neutral-600 hover:bg-neutral-50"
                }`}
              >
                <div className="flex items-center gap-0.5">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star
                      key={i}
                      className={`h-3.5 w-3.5 ${
                        i < rating
                          ? "fill-glam-500 text-glam-500"
                          : "text-neutral-200"
                      }`}
                    />
                  ))}
                </div>
                <span>& up</span>
              </button>
            ))}
          </div>
        </div>

        {/* Availability */}
        <div>
          <label className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-neutral-600 transition-colors hover:bg-neutral-50">
            <input
              type="checkbox"
              checked={filters.is_available || false}
              onChange={(e) =>
                onFilterChange({
                  ...filters,
                  is_available: e.target.checked || undefined,
                  page: 1,
                })
              }
              className="rounded border-neutral-300 text-rose-500 focus:ring-rose-200"
            />
            <span>Available now only</span>
          </label>
        </div>

        {/* Apply (Mobile) */}
        <div className="lg:hidden">
          <Button variant="primary" className="w-full" onClick={onToggle}>
            Apply Filters
          </Button>
        </div>
      </div>
    </div>
  );
}
