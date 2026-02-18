import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { Ionicons } from '@expo/vector-icons';
import { RootStackParamList, Booking, BookingStatus } from '../../types';
import { useClientBookings } from '../../hooks/useBookings';
import BookingCard from '../../components/BookingCard';
import LoadingSpinner from '../../components/ui/LoadingSpinner';

type BookingsNav = StackNavigationProp<RootStackParamList>;

const STATUS_TABS: { key: BookingStatus | 'all'; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'pending', label: 'Pending' },
  { key: 'confirmed', label: 'Confirmed' },
  { key: 'completed', label: 'Completed' },
  { key: 'cancelled', label: 'Cancelled' },
];

export default function BookingsScreen() {
  const navigation = useNavigation<BookingsNav>();
  const [activeTab, setActiveTab] = useState<BookingStatus | 'all'>('all');

  const { data: bookings, isLoading, refetch, isRefetching } =
    useClientBookings(activeTab === 'all' ? undefined : activeTab);

  const handleBookingPress = (bookingId: number) => {
    navigation.navigate('BookingDetail', { bookingId });
  };

  const renderBooking = ({ item }: { item: Booking }) => (
    <BookingCard booking={item} onPress={() => handleBookingPress(item.id)} />
  );

  return (
    <View style={styles.container}>
      {/* Status Tabs */}
      <View style={styles.tabsContainer}>
        <FlatList
          data={STATUS_TABS}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.tabsContent}
          keyExtractor={(item) => item.key}
          renderItem={({ item: tab }) => (
            <TouchableOpacity
              style={[
                styles.tab,
                activeTab === tab.key && styles.tabActive,
              ]}
              onPress={() => setActiveTab(tab.key)}
            >
              <Text
                style={[
                  styles.tabText,
                  activeTab === tab.key && styles.tabTextActive,
                ]}
              >
                {tab.label}
              </Text>
            </TouchableOpacity>
          )}
        />
      </View>

      {/* Bookings List */}
      {isLoading ? (
        <LoadingSpinner message="Loading bookings..." />
      ) : (
        <FlatList
          data={bookings?.results ?? []}
          renderItem={renderBooking}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor="#BE185D"
              colors={['#BE185D']}
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Ionicons name="calendar-outline" size={56} color="#D1D5DB" />
              <Text style={styles.emptyTitle}>No bookings yet</Text>
              <Text style={styles.emptySubtitle}>
                Discover amazing makeup artists and book your first appointment!
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFF7F8',
  },
  tabsContainer: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#FCE7F3',
  },
  tabsContent: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
  },
  tab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F9FAFB',
  },
  tabActive: {
    backgroundColor: '#BE185D',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  tabTextActive: {
    color: '#FFFFFF',
  },
  listContent: {
    padding: 16,
    paddingBottom: 24,
  },
  emptyState: {
    alignItems: 'center',
    paddingTop: 80,
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#6B7280',
    marginTop: 16,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
});
