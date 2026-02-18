import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Booking } from '../types';

interface CreateBookingData {
  artist: string;
  service: string;
  booking_date: string;
  start_time: string;
  end_time: string;
  location: string;
  client_notes?: string;
}

export function useBookings(status?: string) {
  return useQuery({
    queryKey: ['bookings', status],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (status && status !== 'all') params.status = status;

      const response = await api.get('/bookings/bookings/', { params });
      return response.data.results || response.data;
    },
  });
}

export function useBookingDetail(bookingId: string) {
  return useQuery({
    queryKey: ['booking', bookingId],
    queryFn: async () => {
      const response = await api.get(`/bookings/bookings/${bookingId}/`);
      return response.data;
    },
    enabled: !!bookingId,
  });
}

export function useCreateBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateBookingData) => {
      const response = await api.post('/bookings/bookings/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] });
    },
  });
}

export function useBookingAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      bookingId,
      action,
      data,
    }: {
      bookingId: string;
      action: 'accept' | 'reject' | 'complete' | 'cancel';
      data?: Record<string, string>;
    }) => {
      const response = await api.post(
        `/bookings/bookings/${bookingId}/${action}/`,
        data || {}
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] });
      queryClient.invalidateQueries({ queryKey: ['booking', variables.bookingId] });
    },
  });
}

export function useCheckAvailability() {
  return useMutation({
    mutationFn: async (data: {
      artist: string;
      booking_date: string;
      start_time: string;
      end_time: string;
    }) => {
      const response = await api.post('/bookings/bookings/check_availability/', data);
      return response.data;
    },
  });
}

export function useCreateReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      booking: string;
      rating: number;
      comment: string;
    }) => {
      const response = await api.post('/reviews/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] });
    },
  });
}
