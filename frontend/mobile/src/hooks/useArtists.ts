import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { ArtistProfile } from '../types';

interface ArtistFilters {
  search?: string;
  location?: string;
  specialties?: string;
  min_rating?: number;
  min_price?: number;
  max_price?: number;
  is_available?: boolean;
  ordering?: string;
}

export function useArtists(filters: ArtistFilters = {}) {
  return useQuery({
    queryKey: ['artists', filters],
    queryFn: async () => {
      const params: Record<string, string> = {};
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
          params[key] = String(value);
        }
      });

      const response = await api.get('/artists/artists/', { params });
      return response.data.results || response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useArtistDetail(artistId: string) {
  return useQuery({
    queryKey: ['artist', artistId],
    queryFn: async () => {
      const response = await api.get(`/artists/artists/${artistId}/`);
      return response.data;
    },
    enabled: !!artistId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useArtistPortfolio(artistId: string) {
  return useQuery({
    queryKey: ['artist-portfolio', artistId],
    queryFn: async () => {
      const response = await api.get('/artists/portfolio/', {
        params: { artist: artistId },
      });
      return response.data.results || response.data;
    },
    enabled: !!artistId,
  });
}

export function useArtistReviews(artistId: string) {
  return useQuery({
    queryKey: ['artist-reviews', artistId],
    queryFn: async () => {
      const response = await api.get('/reviews/', {
        params: { artist: artistId },
      });
      return response.data.results || response.data;
    },
    enabled: !!artistId,
  });
}

export function useArtistServices(artistId: string) {
  return useQuery({
    queryKey: ['artist-services', artistId],
    queryFn: async () => {
      const response = await api.get('/services/', {
        params: { artist: artistId },
      });
      return response.data.results || response.data;
    },
    enabled: !!artistId,
  });
}

export function useFavorites() {
  return useQuery({
    queryKey: ['favorites'],
    queryFn: async () => {
      const response = await api.get('/artists/favorites/');
      return response.data.results || response.data;
    },
  });
}
