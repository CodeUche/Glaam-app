import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  Alert,
  TextInput,
} from 'react-native';
import { RouteProp, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { RootStackParamList, BookingStatus } from '../../types';
import { useBookingDetail, useCancelBooking, useSubmitReview } from '../../hooks/useBookings';
import BookingStatusBadge from '../../components/BookingStatusBadge';
import StarRating from '../../components/StarRating';
import Button from '../../components/ui/Button';
import LoadingSpinner from '../../components/ui/LoadingSpinner';

type BookingDetailRoute = RouteProp<RootStackParamList, 'BookingDetail'>;

const TIMELINE_STATUSES: BookingStatus[] = [
  'pending',
  'confirmed',
  'in_progress',
  'completed',
];

export default function BookingDetailScreen() {
  const route = useRoute<BookingDetailRoute>();
  const { bookingId } = route.params;
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewComment, setReviewComment] = useState('');

  const { data: booking, isLoading } = useBookingDetail(bookingId);
  const cancelMutation = useCancelBooking();
  const reviewMutation = useSubmitReview();

  if (isLoading || !booking) {
    return <LoadingSpinner message="Loading booking details..." />;
  }

  const handleCancel = () => {
    Alert.alert(
      'Cancel Booking',
      'Are you sure you want to cancel this booking?',
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Yes, Cancel',
          style: 'destructive',
          onPress: () => cancelMutation.mutate(bookingId),
        },
      ],
    );
  };

  const handleSubmitReview = () => {
    if (!reviewComment.trim()) {
      Alert.alert('Review', 'Please enter a comment.');
      return;
    }
    reviewMutation.mutate(
      {
        bookingId,
        data: { rating: reviewRating, comment: reviewComment },
      },
      {
        onSuccess: () => {
          Alert.alert('Thank you!', 'Your review has been submitted.');
          setReviewComment('');
        },
      },
    );
  };

  const currentStatusIndex = TIMELINE_STATUSES.indexOf(booking.status);
  const canCancel = ['pending', 'confirmed'].includes(booking.status);
  const canReview =
    booking.status === 'completed' && !booking.review;

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Artist Info */}
      <View style={styles.artistSection}>
        <Image
          source={
            booking.artist.user.avatar
              ? { uri: booking.artist.user.avatar }
              : require('../../../assets/default-avatar.png')
          }
          style={styles.artistAvatar}
        />
        <View style={styles.artistInfo}>
          <Text style={styles.artistName}>
            {booking.artist.user.full_name}
          </Text>
          <Text style={styles.serviceName}>{booking.service.name}</Text>
        </View>
        <BookingStatusBadge status={booking.status} />
      </View>

      {/* Status Timeline */}
      <View style={styles.timelineSection}>
        <Text style={styles.sectionTitle}>Booking Status</Text>
        <View style={styles.timeline}>
          {TIMELINE_STATUSES.map((status, index) => {
            const isActive = index <= currentStatusIndex;
            const isCurrent = index === currentStatusIndex;
            return (
              <View key={status} style={styles.timelineItem}>
                <View
                  style={[
                    styles.timelineDot,
                    isActive && styles.timelineDotActive,
                    isCurrent && styles.timelineDotCurrent,
                  ]}
                >
                  {isActive && (
                    <Ionicons name="checkmark" size={14} color="#FFFFFF" />
                  )}
                </View>
                {index < TIMELINE_STATUSES.length - 1 && (
                  <View
                    style={[
                      styles.timelineLine,
                      isActive && styles.timelineLineActive,
                    ]}
                  />
                )}
                <Text
                  style={[
                    styles.timelineLabel,
                    isActive && styles.timelineLabelActive,
                  ]}
                >
                  {status.replace('_', ' ').replace(/\b\w/g, (c) =>
                    c.toUpperCase(),
                  )}
                </Text>
              </View>
            );
          })}
        </View>
      </View>

      {/* Booking Details */}
      <View style={styles.detailsSection}>
        <Text style={styles.sectionTitle}>Details</Text>
        <View style={styles.detailCard}>
          <View style={styles.detailRow}>
            <Ionicons name="calendar-outline" size={18} color="#BE185D" />
            <Text style={styles.detailLabel}>Date</Text>
            <Text style={styles.detailValue}>
              {format(new Date(booking.booking_date), 'EEEE, MMM dd, yyyy')}
            </Text>
          </View>
          <View style={styles.detailRow}>
            <Ionicons name="time-outline" size={18} color="#BE185D" />
            <Text style={styles.detailLabel}>Time</Text>
            <Text style={styles.detailValue}>{booking.booking_time}</Text>
          </View>
          <View style={styles.detailRow}>
            <Ionicons name="location-outline" size={18} color="#BE185D" />
            <Text style={styles.detailLabel}>Location</Text>
            <Text style={styles.detailValue}>{booking.location}</Text>
          </View>
          <View style={styles.detailRow}>
            <Ionicons name="cash-outline" size={18} color="#BE185D" />
            <Text style={styles.detailLabel}>Total</Text>
            <Text style={styles.detailPrice}>${booking.total_price}</Text>
          </View>
        </View>

        {booking.notes ? (
          <View style={styles.notesContainer}>
            <Text style={styles.notesLabel}>Notes</Text>
            <Text style={styles.notesText}>{booking.notes}</Text>
          </View>
        ) : null}
      </View>

      {/* Actions */}
      {canCancel && (
        <View style={styles.actionsSection}>
          <Button
            title="Cancel Booking"
            variant="outline"
            onPress={handleCancel}
            loading={cancelMutation.isPending}
          />
        </View>
      )}

      {/* Review Section */}
      {canReview && (
        <View style={styles.reviewSection}>
          <Text style={styles.sectionTitle}>Leave a Review</Text>
          <View style={styles.reviewCard}>
            <Text style={styles.reviewLabel}>Rating</Text>
            <StarRating
              rating={reviewRating}
              interactive
              onRatingChange={setReviewRating}
              size={32}
            />
            <Text style={styles.reviewLabel}>Comment</Text>
            <TextInput
              style={styles.reviewInput}
              placeholder="Share your experience..."
              placeholderTextColor="#9CA3AF"
              multiline
              numberOfLines={4}
              textAlignVertical="top"
              value={reviewComment}
              onChangeText={setReviewComment}
            />
            <Button
              title="Submit Review"
              onPress={handleSubmitReview}
              loading={reviewMutation.isPending}
              style={styles.reviewButton}
            />
          </View>
        </View>
      )}

      {/* Existing Review */}
      {booking.review && (
        <View style={styles.reviewSection}>
          <Text style={styles.sectionTitle}>Your Review</Text>
          <View style={styles.existingReview}>
            <StarRating rating={booking.review.rating} size={18} />
            <Text style={styles.existingReviewText}>
              {booking.review.comment}
            </Text>
          </View>
        </View>
      )}

      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFF7F8',
  },
  artistSection: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#FCE7F3',
  },
  artistAvatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#FCE7F3',
  },
  artistInfo: {
    flex: 1,
    marginLeft: 14,
  },
  artistName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
  },
  serviceName: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  timelineSection: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 16,
  },
  timeline: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  timelineItem: {
    alignItems: 'center',
    flex: 1,
  },
  timelineDot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#E5E7EB',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1,
  },
  timelineDotActive: {
    backgroundColor: '#BE185D',
  },
  timelineDotCurrent: {
    borderWidth: 3,
    borderColor: '#FCE7F3',
  },
  timelineLine: {
    position: 'absolute',
    top: 14,
    left: '50%',
    width: '100%',
    height: 3,
    backgroundColor: '#E5E7EB',
  },
  timelineLineActive: {
    backgroundColor: '#BE185D',
  },
  timelineLabel: {
    fontSize: 11,
    color: '#9CA3AF',
    marginTop: 6,
    textAlign: 'center',
    fontWeight: '500',
  },
  timelineLabelActive: {
    color: '#BE185D',
    fontWeight: '700',
  },
  detailsSection: {
    paddingHorizontal: 20,
  },
  detailCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#F9FAFB',
  },
  detailLabel: {
    flex: 1,
    marginLeft: 10,
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  detailValue: {
    fontSize: 14,
    color: '#1F2937',
    fontWeight: '600',
  },
  detailPrice: {
    fontSize: 18,
    color: '#BE185D',
    fontWeight: '800',
  },
  notesContainer: {
    marginTop: 16,
    backgroundColor: '#FFF1F2',
    borderRadius: 12,
    padding: 14,
  },
  notesLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#BE185D',
    marginBottom: 4,
  },
  notesText: {
    fontSize: 14,
    color: '#4B5563',
    lineHeight: 20,
  },
  actionsSection: {
    padding: 20,
  },
  reviewSection: {
    padding: 20,
  },
  reviewCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 20,
  },
  reviewLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
    marginTop: 12,
  },
  reviewInput: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 14,
    fontSize: 15,
    color: '#1F2937',
    minHeight: 100,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  reviewButton: {
    marginTop: 16,
  },
  existingReview: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
  },
  existingReviewText: {
    fontSize: 14,
    color: '#4B5563',
    marginTop: 8,
    lineHeight: 20,
  },
  bottomSpacer: {
    height: 30,
  },
});
