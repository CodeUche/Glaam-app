"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Users, Frown } from "lucide-react";
import api from "@/lib/api";
import type { ArtistProfile, ArtistFilters as FiltersType, PaginatedResponse } from "@/types";
import ArtistCard from "@/components/artists/ArtistCard";
import ArtistFilters from "@/components/artists/ArtistFilters";
import Button from "@/components/ui/Button";

export default function ArtistsPage() {
  const [filters, setFilters] = useState<FiltersType>({ page: 1 });
  const [filtersOpen, setFiltersOpen] = useState(false);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["artists", filters],
    queryFn: async () => {
      const params: Record<string, string | number | boolean> = {};
      if (filters.search) params.search = filters.search;
      if (filters.specialty) params.specialty = filters.specialty;
      if (filters.min_price !== undefined) params.min_price = filters.min_price;
      if (filters.max_price !== undefined) params.max_price = filters.max_price;
      if (filters.min_rating !== undefined) params.min_rating = filters.min_rating;
      if (filters.location) params.location = filters.location;
      if (filters.is_available) params.is_available = true;
      if (filters.ordering) params.ordering = filters.ordering;
      if (filters.page) params.page = filters.page;
      params.page_size = 12;

      const { data } = await api.get<PaginatedResponse<ArtistProfile>>(
        "/artists/",
        { params }
      );
      return data;
    },
  });

  const totalPages = data ? Math.ceil(data.count / 12) : 0;
  const currentPage = filters.page || 1;

  return (
    <div className="min-h-screen bg-neutral-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold text-neutral-900 sm:text-4xl">
            Discover Artists
          </h1>
          <p className="mt-2 text-neutral-500">
            Find the perfect makeup artist for your next look
            {data && (
              <span className="ml-2 text-sm text-neutral-400">
                ({data.count} artist{data.count !== 1 ? "s" : ""} found)
              </span>
            )}
          </p>
        </div>

        <div className="flex flex-col gap-8 lg:flex-row">
          {/* Sidebar Filters */}
          <aside className="w-full shrink-0 lg:w-72">
            <ArtistFilters
              filters={filters}
              onFilterChange={setFilters}
              isOpen={filtersOpen}
              onToggle={() => setFiltersOpen(!filtersOpen)}
            />
          </aside>

          {/* Main Content */}
          <div className="flex-1">
            {isLoading ? (
              <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-80 animate-pulse rounded-2xl bg-neutral-100"
                  />
                ))}
              </div>
            ) : data && data.results.length > 0 ? (
              <>
                <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                  {data.results.map((artist) => (
                    <ArtistCard key={artist.id} artist={artist} />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="mt-10 flex items-center justify-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={currentPage === 1 || isFetching}
                      onClick={() =>
                        setFilters({ ...filters, page: currentPage - 1 })
                      }
                    >
                      Previous
                    </Button>

                    <div className="flex items-center gap-1">
                      {Array.from({ length: Math.min(totalPages, 5) }).map(
                        (_, i) => {
                          let pageNum: number;
                          if (totalPages <= 5) {
                            pageNum = i + 1;
                          } else if (currentPage <= 3) {
                            pageNum = i + 1;
                          } else if (currentPage >= totalPages - 2) {
                            pageNum = totalPages - 4 + i;
                          } else {
                            pageNum = currentPage - 2 + i;
                          }

                          return (
                            <button
                              key={pageNum}
                              onClick={() =>
                                setFilters({ ...filters, page: pageNum })
                              }
                              className={`flex h-9 w-9 items-center justify-center rounded-lg text-sm font-medium transition-colors ${
                                pageNum === currentPage
                                  ? "bg-rose-500 text-white"
                                  : "text-neutral-600 hover:bg-neutral-100"
                              }`}
                            >
                              {pageNum}
                            </button>
                          );
                        }
                      )}
                    </div>

                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={currentPage === totalPages || isFetching}
                      onClick={() =>
                        setFilters({ ...filters, page: currentPage + 1 })
                      }
                    >
                      Next
                    </Button>
                  </div>
                )}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-neutral-100 bg-white py-20 text-center">
                <Frown className="mb-4 h-12 w-12 text-neutral-300" />
                <h3 className="mb-2 text-lg font-semibold text-neutral-700">
                  No artists found
                </h3>
                <p className="mb-6 max-w-sm text-sm text-neutral-400">
                  Try adjusting your filters or search terms to find more makeup
                  artists.
                </p>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setFilters({ page: 1 });
                  }}
                >
                  Clear Filters
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
