import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { api } from '../../lib/api';
import { Booking } from '../../types';
import { BookingStatusBadge } from '../../components/BookingStatusBadge';

const COLORS = {
  primary: '#E11D48',
  background: '#FFF1F2',
  white: '#FFFFFF',
  gray: '#6B7280',
  lightGray: '#F3F4F6',
  dark: '#111827',
  green: '#10B981',
  amber: '#F59E0B',
};

export default function DashboardScreen({ navigation }: any) {
  const [pendingBookings, setPendingBookings] = useState<Booking[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    completed: 0,
    earnings: 0,
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [pendingRes, allRes] = await Promise.all([
        api.get('/bookings/bookings/', { params: { status: 'pending' } }),
        api.get('/bookings/bookings/'),
      ]);

      const pending = pendingRes.data.results || pendingRes.data;
      const all = allRes.data.results || allRes.data;

      setPendingBookings(pending);
      setStats({
        total: all.length,
        pending: pending.length,
        completed: all.filter((b: Booking) => b.status === 'completed').length,
        earnings: all
          .filter((b: Booking) => b.status === 'completed')
          .reduce((sum: number, b: Booking) => sum + parseFloat(String(b.total_price)), 0),
      });
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleBookingAction = async (bookingId: string, action: 'accept' | 'reject') => {
    try {
      await api.post(`/bookings/bookings/${bookingId}/${action}/`);
      fetchData();
    } catch (error) {
      console.error(`Failed to ${action} booking:`, error);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchData(); }} />
      }
    >
      <Text style={styles.title}>Dashboard</Text>

      {/* Stats */}
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{stats.total}</Text>
          <Text style={styles.statLabel}>Total Bookings</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, { color: COLORS.amber }]}>{stats.pending}</Text>
          <Text style={styles.statLabel}>Pending</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, { color: COLORS.green }]}>{stats.completed}</Text>
          <Text style={styles.statLabel}>Completed</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, { color: COLORS.primary }]}>
            ${stats.earnings.toFixed(0)}
          </Text>
          <Text style={styles.statLabel}>Earnings</Text>
        </View>
      </View>

      {/* Pending Bookings */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          Pending Requests ({pendingBookings.length})
        </Text>
        {pendingBookings.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyText}>No pending requests</Text>
          </View>
        ) : (
          pendingBookings.map((booking) => (
            <View key={booking.id} style={styles.bookingCard}>
              <View style={styles.bookingHeader}>
                <Text style={styles.bookingNumber}>{booking.booking_number}</Text>
                <Text style={styles.bookingPrice}>${booking.total_price}</Text>
              </View>
              <Text style={styles.bookingDetail}>
                {booking.booking_date} at {booking.start_time}
              </Text>
              <Text style={styles.bookingDetail}>{booking.location}</Text>
              <View style={styles.actionRow}>
                <TouchableOpacity
                  style={styles.acceptButton}
                  onPress={() => handleBookingAction(booking.id, 'accept')}
                >
                  <Text style={styles.acceptButtonText}>Accept</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.declineButton}
                  onPress={() => handleBookingAction(booking.id, 'reject')}
                >
                  <Text style={styles.declineButtonText}>Decline</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.lightGray, padding: 16 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 28, fontWeight: '700', color: COLORS.dark, marginBottom: 20, marginTop: 8 },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginBottom: 24 },
  statCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 16,
    width: '47%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  statValue: { fontSize: 28, fontWeight: '700', color: COLORS.dark },
  statLabel: { fontSize: 13, color: COLORS.gray, marginTop: 4 },
  section: { marginBottom: 24 },
  sectionTitle: { fontSize: 18, fontWeight: '600', color: COLORS.dark, marginBottom: 12 },
  emptyCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
  },
  emptyText: { color: COLORS.gray, fontSize: 15 },
  bookingCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  bookingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  bookingNumber: { fontSize: 16, fontWeight: '600', color: COLORS.dark },
  bookingPrice: { fontSize: 18, fontWeight: '700', color: COLORS.primary },
  bookingDetail: { fontSize: 14, color: COLORS.gray, marginBottom: 4 },
  actionRow: { flexDirection: 'row', gap: 12, marginTop: 12 },
  acceptButton: {
    flex: 1,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  acceptButtonText: { color: COLORS.white, fontWeight: '600', fontSize: 14 },
  declineButton: {
    flex: 1,
    backgroundColor: COLORS.white,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  declineButtonText: { color: COLORS.gray, fontWeight: '600', fontSize: 14 },
});
