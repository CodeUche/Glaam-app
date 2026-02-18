import React from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { format } from 'date-fns';
import { Review } from '../types';
import StarRating from './StarRating';

interface ReviewCardProps {
  review: Review;
}

export default function ReviewCard({ review }: ReviewCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Image
          source={
            review.client.avatar
              ? { uri: review.client.avatar }
              : require('../../assets/default-avatar.png')
          }
          style={styles.avatar}
        />
        <View style={styles.headerText}>
          <Text style={styles.name}>{review.client.full_name}</Text>
          <Text style={styles.date}>
            {format(new Date(review.created_at), 'MMM dd, yyyy')}
          </Text>
        </View>
        <StarRating rating={review.rating} size={14} />
      </View>

      {review.comment ? (
        <Text style={styles.comment}>{review.comment}</Text>
      ) : null}

      {review.images && review.images.length > 0 && (
        <View style={styles.imagesRow}>
          {review.images.slice(0, 4).map((img, index) => (
            <Image key={index} source={{ uri: img }} style={styles.reviewImage} />
          ))}
          {review.images.length > 4 && (
            <View style={styles.moreImages}>
              <Text style={styles.moreImagesText}>
                +{review.images.length - 4}
              </Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#F3F4F6',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#FCE7F3',
  },
  headerText: {
    flex: 1,
    marginLeft: 10,
  },
  name: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  date: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 1,
  },
  comment: {
    fontSize: 14,
    color: '#4B5563',
    lineHeight: 20,
  },
  imagesRow: {
    flexDirection: 'row',
    marginTop: 10,
  },
  reviewImage: {
    width: 60,
    height: 60,
    borderRadius: 8,
    marginRight: 6,
    backgroundColor: '#FCE7F3',
  },
  moreImages: {
    width: 60,
    height: 60,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  moreImagesText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
});
