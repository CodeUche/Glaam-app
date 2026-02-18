import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { Booking } from '../types';
import BookingStatusBadge from './BookingStatusBadge';

interface BookingCardProps {
  booking: Booking;
  onPress: () => void;
  showArtist?: boolean;
}

export default function BookingCard({
  booking,
  onPress,
  showArtist = true,
}: BookingCardProps) {
  const bookingDate = new Date(booking.booking_date);

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <View style={styles.topRow}>
        {showArtist && (
          <View style={styles.artistInfo}>
            <Image
              source={
                booking.artist.user.avatar
                  ? { uri: booking.artist.user.avatar }
                  : require('../../assets/default-avatar.png')
              }
              style={styles.avatar}
            />
            <View style={styles.artistText}>
              <Text style={styles.artistName} numberOfLines={1}>
                {booking.artist.user.full_name}
              </Text>
              <Text style={styles.serviceName} numberOfLines={1}>
                {booking.service.name}
              </Text>
            </View>
          </View>
        )}
        <BookingStatusBadge status={booking.status} />
      </View>

      <View style={styles.divider} />

      <View style={styles.detailsRow}>
        <View style={styles.detailItem}>
          <Ionicons name="calendar-outline" size={16} color="#6B7280" />
          <Text style={styles.detailText}>
            {format(bookingDate, 'MMM dd, yyyy')}
          </Text>
        </View>
        <View style={styles.detailItem}>
          <Ionicons name="time-outline" size={16} color="#6B7280" />
          <Text style={styles.detailText}>{booking.booking_time}</Text>
        </View>
        <View style={styles.detailItem}>
          <Ionicons name="cash-outline" size={16} color="#6B7280" />
          <Text style={styles.priceText}>${booking.total_price}</Text>
        </View>
      </View>

      {booking.location && (
        <View style={styles.locationRow}>
          <Ionicons name="location-outline" size={14} color="#9CA3AF" />
          <Text style={styles.locationText} numberOfLines={1}>
            {booking.location}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#BE185D',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  artistInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: 10,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#FCE7F3',
  },
  artistText: {
    marginLeft: 12,
    flex: 1,
  },
  artistName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
  },
  serviceName: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: '#F3F4F6',
    marginVertical: 12,
  },
  detailsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  detailText: {
    marginLeft: 6,
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '500',
  },
  priceText: {
    marginLeft: 6,
    fontSize: 14,
    color: '#BE185D',
    fontWeight: '700',
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
  },
  locationText: {
    marginLeft: 4,
    fontSize: 12,
    color: '#9CA3AF',
  },
});
