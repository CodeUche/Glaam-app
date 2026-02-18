import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { api } from '../../lib/api';
import { Booking } from '../../types';
import { BookingCard } from '../../components/BookingCard';

const COLORS = {
  primary: '#E11D48',
  white: '#FFFFFF',
  gray: '#6B7280',
  lightGray: '#F3F4F6',
  dark: '#111827',
};

const STATUS_TABS = ['all', 'pending', 'accepted', 'completed', 'cancelled'] as const;

export default function ManageBookingsScreen({ navigation }: any) {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('all');

  const fetchBookings = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (activeTab !== 'all') params.status = activeTab;

      const response = await api.get('/bookings/bookings/', { params });
      setBookings(response.data.results || response.data);
    } catch (error) {
      console.error('Failed to fetch bookings:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeTab]);

  useEffect(() => {
    setLoading(true);
    fetchBookings();
  }, [fetchBookings]);

  const handleAction = async (bookingId: string, action: string) => {
    const actionLabels: Record<string, string> = {
      accept: 'Accept',
      reject: 'Decline',
      complete: 'Complete',
      cancel: 'Cancel',
    };

    Alert.alert(
      `${actionLabels[action]} Booking`,
      `Are you sure you want to ${action} this booking?`,
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Yes',
          onPress: async () => {
            try {
              await api.post(`/bookings/bookings/${bookingId}/${action}/`);
              fetchBookings();
            } catch (error) {
              Alert.alert('Error', `Failed to ${action} booking`);
            }
          },
        },
      ]
    );
  };

  const renderBooking = ({ item }: { item: Booking }) => (
    <View style={styles.bookingWrapper}>
      <BookingCard
        booking={item}
        onPress={() => navigation.navigate('BookingDetail', { bookingId: item.id })}
      />
      {item.status === 'pending' && (
        <View style={styles.actionRow}>
          <TouchableOpacity
            style={styles.acceptBtn}
            onPress={() => handleAction(item.id, 'accept')}
          >
            <Text style={styles.acceptText}>Accept</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.declineBtn}
            onPress={() => handleAction(item.id, 'reject')}
          >
            <Text style={styles.declineText}>Decline</Text>
          </TouchableOpacity>
        </View>
      )}
      {item.status === 'accepted' && (
        <TouchableOpacity
          style={styles.completeBtn}
          onPress={() => handleAction(item.id, 'complete')}
        >
          <Text style={styles.acceptText}>Mark Complete</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Tabs */}
      <FlatList
        horizontal
        data={STATUS_TABS}
        keyExtractor={(item) => item}
        showsHorizontalScrollIndicator={false}
        style={styles.tabBar}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.tab, activeTab === item && styles.activeTab]}
            onPress={() => setActiveTab(item)}
          >
            <Text style={[styles.tabText, activeTab === item && styles.activeTabText]}>
              {item.charAt(0).toUpperCase() + item.slice(1)}
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* Bookings List */}
      {loading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={bookings}
          keyExtractor={(item) => item.id}
          renderItem={renderBooking}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchBookings(); }} />
          }
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={styles.emptyText}>No bookings found</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.lightGray },
  tabBar: { maxHeight: 50, paddingHorizontal: 12, paddingTop: 12 },
  tab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: COLORS.white,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  activeTab: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  tabText: { fontSize: 14, color: COLORS.gray, fontWeight: '500' },
  activeTabText: { color: COLORS.white },
  listContent: { padding: 16 },
  bookingWrapper: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    marginBottom: 12,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  actionRow: { flexDirection: 'row', gap: 10, marginTop: 12 },
  acceptBtn: {
    flex: 1,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  acceptText: { color: COLORS.white, fontWeight: '600' },
  declineBtn: {
    flex: 1,
    backgroundColor: COLORS.white,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  declineText: { color: COLORS.gray, fontWeight: '600' },
  completeBtn: {
    backgroundColor: '#10B981',
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
    marginTop: 12,
  },
  empty: { paddingVertical: 40, alignItems: 'center' },
  emptyText: { color: COLORS.gray, fontSize: 16 },
});
