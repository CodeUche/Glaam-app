import React from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ArtistProfile } from '../types';
import StarRating from './StarRating';

interface ArtistCardProps {
  artist: ArtistProfile;
  onPress: () => void;
  onFavoriteToggle?: () => void;
  isFavorite?: boolean;
}

export default function ArtistCard({
  artist,
  onPress,
  onFavoriteToggle,
  isFavorite = false,
}: ArtistCardProps) {
  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <Image
        source={
          artist.user.avatar
            ? { uri: artist.user.avatar }
            : require('../../assets/default-avatar.png')
        }
        style={styles.avatar}
        defaultSource={require('../../assets/default-avatar.png')}
      />

      {onFavoriteToggle && (
        <TouchableOpacity
          style={styles.favoriteButton}
          onPress={onFavoriteToggle}
        >
          <Ionicons
            name={isFavorite ? 'heart' : 'heart-outline'}
            size={22}
            color={isFavorite ? '#EF4444' : '#FFFFFF'}
          />
        </TouchableOpacity>
      )}

      <View style={styles.content}>
        <Text style={styles.name} numberOfLines={1}>
          {artist.user.full_name}
        </Text>

        <View style={styles.ratingRow}>
          <StarRating rating={artist.average_rating} size={14} />
          <Text style={styles.ratingText}>
            {artist.average_rating.toFixed(1)} ({artist.total_reviews})
          </Text>
        </View>

        <View style={styles.specialtiesRow}>
          {artist.specialties.slice(0, 2).map((specialty, index) => (
            <View key={index} style={styles.specialtyBadge}>
              <Text style={styles.specialtyText}>{specialty}</Text>
            </View>
          ))}
        </View>

        <View style={styles.bottomRow}>
          <Text style={styles.price}>
            From ${artist.hourly_rate}/hr
          </Text>
          {artist.is_available && (
            <View style={styles.availableBadge}>
              <View style={styles.availableDot} />
              <Text style={styles.availableText}>Available</Text>
            </View>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 16,
    shadowColor: '#BE185D',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 4,
  },
  avatar: {
    width: '100%',
    height: 200,
    backgroundColor: '#FCE7F3',
  },
  favoriteButton: {
    position: 'absolute',
    top: 12,
    right: 12,
    backgroundColor: 'rgba(0,0,0,0.35)',
    borderRadius: 20,
    padding: 8,
  },
  content: {
    padding: 14,
  },
  name: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 4,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  ratingText: {
    marginLeft: 6,
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '500',
  },
  specialtiesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 10,
  },
  specialtyBadge: {
    backgroundColor: '#FCE7F3',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 6,
    marginBottom: 4,
  },
  specialtyText: {
    fontSize: 12,
    color: '#BE185D',
    fontWeight: '600',
  },
  bottomRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  price: {
    fontSize: 16,
    fontWeight: '700',
    color: '#BE185D',
  },
  availableBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  availableDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10B981',
    marginRight: 5,
  },
  availableText: {
    fontSize: 12,
    color: '#10B981',
    fontWeight: '600',
  },
});
