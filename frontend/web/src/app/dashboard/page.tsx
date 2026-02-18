'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';
import { Booking } from '@/types';
import { Navbar } from '@/components/layout/Navbar';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { BookingStatusBadge } from '@/components/bookings/BookingStatusBadge';

interface DashboardStats {
  total_bookings: number;
  pending_bookings: number;
  completed_bookings: number;
  total_earnings: number;
  average_rating: number;
  total_reviews: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pendingBookings, setPendingBookings] = useState<Booking[]>([]);
  const [recentBookings, setRecentBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'artist') {
      router.push('/');
      return;
    }
    fetchDashboardData();
  }, [isAuthenticated, user]);

  const fetchDashboardData = async () => {
    try {
      const [pendingRes, recentRes] = await Promise.all([
        api.get('/bookings/bookings/', { params: { status: 'pending' } }),
        api.get('/bookings/bookings/', { params: { ordering: '-created_at' } }),
      ]);

      const pending = pendingRes.data.results || pendingRes.data;
      const recent = recentRes.data.results || recentRes.data;

      setPendingBookings(pending);
      setRecentBookings(recent.slice(0, 5));

      // Calculate stats from bookings
      setStats({
        total_bookings: recent.length,
        pending_bookings: pending.length,
        completed_bookings: recent.filter((b: Booking) => b.status === 'completed').length,
        total_earnings: recent
          .filter((b: Booking) => b.status === 'completed')
          .reduce((sum: number, b: Booking) => sum + parseFloat(String(b.total_price)), 0),
        average_rating: 0,
        total_reviews: 0,
      });
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBookingAction = async (bookingId: string, action: 'accept' | 'reject') => {
    try {
      await api.post(`/bookings/bookings/${bookingId}/${action}/`);
      fetchDashboardData();
    } catch (error) {
      console.error(`Failed to ${action} booking:`, error);
    }
  };

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex justify-center py-24">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-rose-500" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome back, {user?.first_name}
        </h1>
        <p className="text-gray-500 mb-8">Here's your business overview</p>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card className="p-6">
            <p className="text-sm text-gray-500 mb-1">Total Bookings</p>
            <p className="text-3xl font-bold text-gray-900">{stats?.total_bookings || 0}</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-gray-500 mb-1">Pending Requests</p>
            <p className="text-3xl font-bold text-amber-500">{stats?.pending_bookings || 0}</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-gray-500 mb-1">Completed</p>
            <p className="text-3xl font-bold text-green-600">{stats?.completed_bookings || 0}</p>
          </Card>
          <Card className="p-6">
            <p className="text-sm text-gray-500 mb-1">Total Earnings</p>
            <p className="text-3xl font-bold text-rose-600">
              ${stats?.total_earnings?.toFixed(2) || '0.00'}
            </p>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pending Bookings */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Pending Requests ({pendingBookings.length})
            </h2>
            {pendingBookings.length === 0 ? (
              <Card className="p-6 text-center text-gray-500">
                No pending booking requests
              </Card>
            ) : (
              <div className="space-y-3">
                {pendingBookings.map((booking) => (
                  <Card key={booking.id} className="p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="font-semibold text-gray-900">{booking.booking_number}</p>
                        <p className="text-sm text-gray-600">
                          {formatDate(booking.booking_date)} at {booking.start_time}
                        </p>
                        <p className="text-sm text-gray-600">{booking.location}</p>
                      </div>
                      <p className="font-bold text-rose-600">${booking.total_price}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => handleBookingAction(booking.id, 'accept')}
                      >
                        Accept
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleBookingAction(booking.id, 'reject')}
                      >
                        Decline
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Recent Bookings */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Recent Bookings</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push('/bookings')}
              >
                View All
              </Button>
            </div>
            {recentBookings.length === 0 ? (
              <Card className="p-6 text-center text-gray-500">
                No bookings yet
              </Card>
            ) : (
              <div className="space-y-3">
                {recentBookings.map((booking) => (
                  <Card
                    key={booking.id}
                    className="p-4 cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => router.push(`/bookings/${booking.id}`)}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium text-gray-900">{booking.booking_number}</p>
                        <p className="text-sm text-gray-500">
                          {formatDate(booking.booking_date)}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <p className="font-semibold">${booking.total_price}</p>
                        <BookingStatusBadge status={booking.status} />
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
