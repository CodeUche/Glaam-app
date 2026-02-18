'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';
import { Booking } from '@/types';
import { Navbar } from '@/components/layout/Navbar';
import { BookingStatusBadge } from '@/components/bookings/BookingStatusBadge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';

const STATUS_TIMELINE = [
  { key: 'pending', label: 'Requested', icon: '1' },
  { key: 'accepted', label: 'Confirmed', icon: '2' },
  { key: 'completed', label: 'Completed', icon: '3' },
];

export default function BookingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuthStore();
  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchBooking();
  }, [params.id]);

  const fetchBooking = async () => {
    try {
      const response = await api.get(`/bookings/bookings/${params.id}/`);
      setBooking(response.data);
    } catch (error) {
      console.error('Failed to fetch booking:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (action: string, data?: Record<string, string>) => {
    try {
      setActionLoading(true);
      await api.post(`/bookings/bookings/${params.id}/${action}/`, data || {});
      fetchBooking();
    } catch (error) {
      console.error(`Failed to ${action} booking:`, error);
    } finally {
      setActionLoading(false);
      setShowCancelModal(false);
    }
  };

  const getTimelineStatus = (step: string) => {
    if (!booking) return 'upcoming';
    const statusOrder = ['pending', 'accepted', 'completed'];
    const currentIdx = statusOrder.indexOf(booking.status);
    const stepIdx = statusOrder.indexOf(step);

    if (booking.status === 'cancelled' || booking.status === 'rejected') return 'cancelled';
    if (stepIdx < currentIdx) return 'done';
    if (stepIdx === currentIdx) return 'current';
    return 'upcoming';
  };

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });

  const formatTime = (timeStr: string) => {
    const [hours, minutes] = timeStr.split(':');
    const h = parseInt(hours);
    return `${h > 12 ? h - 12 : h}:${minutes} ${h >= 12 ? 'PM' : 'AM'}`;
  };

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

  if (!booking) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-2xl mx-auto px-4 py-24 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Booking not found</h2>
          <Button onClick={() => router.push('/bookings')}>Back to Bookings</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-3xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <button
              onClick={() => router.push('/bookings')}
              className="text-rose-500 hover:text-rose-600 text-sm mb-2 flex items-center gap-1"
            >
              &larr; Back to Bookings
            </button>
            <h1 className="text-2xl font-bold text-gray-900">
              Booking {booking.booking_number}
            </h1>
          </div>
          <BookingStatusBadge status={booking.status} />
        </div>

        {/* Status Timeline */}
        {booking.status !== 'cancelled' && booking.status !== 'rejected' && (
          <Card className="p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Status</h2>
            <div className="flex items-center justify-between">
              {STATUS_TIMELINE.map((step, idx) => {
                const stepStatus = getTimelineStatus(step.key);
                return (
                  <div key={step.key} className="flex items-center flex-1">
                    <div className="flex flex-col items-center">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                          stepStatus === 'done'
                            ? 'bg-green-500 text-white'
                            : stepStatus === 'current'
                            ? 'bg-rose-500 text-white'
                            : 'bg-gray-200 text-gray-500'
                        }`}
                      >
                        {stepStatus === 'done' ? '✓' : step.icon}
                      </div>
                      <span className="text-xs mt-2 text-gray-600">{step.label}</span>
                    </div>
                    {idx < STATUS_TIMELINE.length - 1 && (
                      <div
                        className={`flex-1 h-0.5 mx-2 ${
                          getTimelineStatus(STATUS_TIMELINE[idx + 1].key) !== 'upcoming'
                            ? 'bg-green-500'
                            : 'bg-gray-200'
                        }`}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </Card>
        )}

        {/* Booking Details */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Booking Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Date</p>
              <p className="font-medium">{formatDate(booking.booking_date)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Time</p>
              <p className="font-medium">
                {formatTime(booking.start_time)} - {formatTime(booking.end_time)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Location</p>
              <p className="font-medium">{booking.location}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Price</p>
              <p className="font-medium text-xl text-rose-600">${booking.total_price}</p>
            </div>
          </div>

          {booking.client_notes && (
            <div className="mt-4 pt-4 border-t">
              <p className="text-sm text-gray-500">Notes</p>
              <p className="text-gray-700">{booking.client_notes}</p>
            </div>
          )}
        </Card>

        {/* Actions */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Actions</h2>
          <div className="flex flex-wrap gap-3">
            {/* Artist actions */}
            {user?.role === 'artist' && booking.status === 'pending' && (
              <>
                <Button
                  onClick={() => handleAction('accept')}
                  disabled={actionLoading}
                >
                  Accept Booking
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleAction('reject', { reason: 'Not available' })}
                  disabled={actionLoading}
                >
                  Decline
                </Button>
              </>
            )}

            {user?.role === 'artist' && booking.status === 'accepted' && (
              <Button
                onClick={() => handleAction('complete')}
                disabled={actionLoading}
              >
                Mark as Completed
              </Button>
            )}

            {/* Client actions */}
            {user?.role === 'client' && booking.status === 'completed' && (
              <Button onClick={() => router.push(`/bookings/${booking.id}/review`)}>
                Leave a Review
              </Button>
            )}

            {/* Cancel (both roles, if pending/accepted) */}
            {['pending', 'accepted'].includes(booking.status) && (
              <Button
                variant="outline"
                className="text-red-600 border-red-300 hover:bg-red-50"
                onClick={() => setShowCancelModal(true)}
                disabled={actionLoading}
              >
                Cancel Booking
              </Button>
            )}
          </div>
        </Card>
      </main>

      {/* Cancel Modal */}
      <Modal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        title="Cancel Booking"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Are you sure you want to cancel this booking? This action cannot be undone.
          </p>
          <textarea
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            placeholder="Reason for cancellation (optional)"
            className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent"
            rows={3}
          />
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setShowCancelModal(false)}>
              Keep Booking
            </Button>
            <Button
              className="bg-red-500 hover:bg-red-600"
              onClick={() => handleAction('cancel', { reason: cancelReason })}
              disabled={actionLoading}
            >
              {actionLoading ? 'Cancelling...' : 'Confirm Cancel'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
