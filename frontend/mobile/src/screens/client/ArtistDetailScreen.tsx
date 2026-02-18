import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  FlatList,
  TouchableOpacity,
  Dimensions,
  Alert,
} from 'react-native';
import { RouteProp, useRoute, useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { RootStackParamList, Service, PortfolioImage } from '../../types';
import { useArtistDetail } from '../../hooks/useArtists';
import StarRating from '../../components/StarRating';
import ReviewCard from '../../components/ReviewCard';
import Button from '../../components/ui/Button';
import LoadingSpinner from '../../components/ui/LoadingSpinner';

type ArtistDetailRoute = RouteProp<RootStackParamList, 'ArtistDetail'>;

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const GALLERY_IMAGE_SIZE = (SCREEN_WIDTH - 48 - 12) / 3;

export default function ArtistDetailScreen() {
  const route = useRoute<ArtistDetailRoute>();
  const navigation = useNavigation();
  const { artistId } = route.params;
  const [selectedService, setSelectedService] = useState<Service | null>(null);

  const { data: artist, isLoading } = useArtistDetail(artistId);

  if (isLoading || !artist) {
    return <LoadingSpinner message="Loading artist profile..." />;
  }

  const handleBookNow = () => {
    if (!selectedService) {
      Alert.alert('Select a Service', 'Please select a service before booking.');
      return;
    }
    Alert.alert(
      'Book Appointment',
      `Book ${selectedService.name} with ${artist.user.full_name} for $${selectedService.price}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm',
          onPress: () => {
            // Navigate to booking confirmation or create booking
            Alert.alert('Success', 'Booking request sent!');
          },
        },
      ],
    );
  };

  return (
    <View style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Hero Image */}
        <View style={styles.heroContainer}>
          <Image
            source={
              artist.user.avatar
                ? { uri: artist.user.avatar }
                : require('../../../assets/default-avatar.png')
            }
            style={styles.heroImage}
          />
          <View style={styles.heroOverlay}>
            <Text style={styles.heroName}>{artist.user.full_name}</Text>
            <View style={styles.heroRating}>
              <StarRating rating={artist.average_rating} size={18} color="#F59E0B" />
              <Text style={styles.heroRatingText}>
                {artist.average_rating.toFixed(1)} ({artist.total_reviews} reviews)
              </Text>
            </View>
          </View>
        </View>

        {/* Quick Stats */}
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{artist.years_of_experience}</Text>
            <Text style={styles.statLabel}>Years Exp.</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{artist.total_bookings}</Text>
            <Text style={styles.statLabel}>Bookings</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>${artist.hourly_rate}</Text>
            <Text style={styles.statLabel}>Per Hour</Text>
          </View>
        </View>

        {/* Bio */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          <Text style={styles.bioText}>{artist.bio}</Text>

          {/* Specialties */}
          <View style={styles.specialtiesRow}>
            {artist.specialties.map((spec, index) => (
              <View key={index} style={styles.specialtyBadge}>
                <Text style={styles.specialtyText}>{spec}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Services */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Services</Text>
          {artist.services
            .filter((s) => s.is_active)
            .map((service) => (
              <TouchableOpacity
                key={service.id}
                style={[
                  styles.serviceCard,
                  selectedService?.id === service.id && styles.serviceCardActive,
                ]}
                onPress={() => setSelectedService(service)}
              >
                <View style={styles.serviceLeft}>
                  <Text style={styles.serviceName}>{service.name}</Text>
                  <Text style={styles.serviceDesc} numberOfLines={2}>
                    {service.description}
                  </Text>
                  <View style={styles.serviceMeta}>
                    <Ionicons name="time-outline" size={14} color="#9CA3AF" />
                    <Text style={styles.serviceDuration}>
                      {service.duration_minutes} min
                    </Text>
                  </View>
                </View>
                <View style={styles.serviceRight}>
                  <Text style={styles.servicePrice}>${service.price}</Text>
                  {selectedService?.id === service.id && (
                    <Ionicons name="checkmark-circle" size={22} color="#BE185D" />
                  )}
                </View>
              </TouchableOpacity>
            ))}
        </View>

        {/* Portfolio Gallery */}
        {artist.portfolio_images.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Portfolio</Text>
            <View style={styles.galleryGrid}>
              {artist.portfolio_images.map((img: PortfolioImage) => (
                <Image
                  key={img.id}
                  source={{ uri: img.image }}
                  style={styles.galleryImage}
                />
              ))}
            </View>
          </View>
        )}

        {/* Reviews */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>
              Reviews ({artist.total_reviews})
            </Text>
          </View>
          {/* Reviews would be loaded separately via a hook; showing placeholder */}
          <Text style={styles.placeholderText}>
            Reviews are loaded when viewing the full profile.
          </Text>
        </View>

        {/* Contact / Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Details</Text>
          <View style={styles.detailRow}>
            <Ionicons name="location-outline" size={18} color="#6B7280" />
            <Text style={styles.detailText}>
              Travels up to {artist.travel_radius_km} km
            </Text>
          </View>
          {artist.instagram_handle && (
            <View style={styles.detailRow}>
              <Ionicons name="logo-instagram" size={18} color="#6B7280" />
              <Text style={styles.detailText}>@{artist.instagram_handle}</Text>
            </View>
          )}
          {artist.certifications.length > 0 && (
            <View style={styles.detailRow}>
              <Ionicons name="ribbon-outline" size={18} color="#6B7280" />
              <Text style={styles.detailText}>
                {artist.certifications.join(', ')}
              </Text>
            </View>
          )}
        </View>

        <View style={styles.bottomSpacer} />
      </ScrollView>

      {/* Bottom Book Button */}
      <View style={styles.bookingBar}>
        <View style={styles.bookingBarLeft}>
          {selectedService ? (
            <>
              <Text style={styles.selectedServiceName}>
                {selectedService.name}
              </Text>
              <Text style={styles.selectedServicePrice}>
                ${selectedService.price}
              </Text>
            </>
          ) : (
            <Text style={styles.selectPrompt}>Select a service above</Text>
          )}
        </View>
        <Button
          title="Book Now"
          onPress={handleBookNow}
          disabled={!selectedService}
          fullWidth={false}
          style={styles.bookButton}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFF7F8',
  },
  heroContainer: {
    position: 'relative',
    height: 280,
  },
  heroImage: {
    width: '100%',
    height: '100%',
    backgroundColor: '#FCE7F3',
  },
  heroOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: 'rgba(0,0,0,0.4)',
  },
  heroName: {
    fontSize: 26,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  heroRating: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  heroRatingText: {
    marginLeft: 8,
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '500',
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    paddingVertical: 18,
    paddingHorizontal: 20,
    justifyContent: 'space-around',
    borderBottomWidth: 1,
    borderBottomColor: '#FCE7F3',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: '800',
    color: '#BE185D',
  },
  statLabel: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
  },
  statDivider: {
    width: 1,
    backgroundColor: '#F3F4F6',
  },
  section: {
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 12,
  },
  bioText: {
    fontSize: 15,
    color: '#4B5563',
    lineHeight: 22,
  },
  specialtiesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 12,
  },
  specialtyBadge: {
    backgroundColor: '#FCE7F3',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
    marginRight: 8,
    marginBottom: 8,
  },
  specialtyText: {
    fontSize: 13,
    color: '#BE185D',
    fontWeight: '600',
  },
  serviceCard: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1.5,
    borderColor: '#F3F4F6',
  },
  serviceCardActive: {
    borderColor: '#BE185D',
    backgroundColor: '#FFF1F2',
  },
  serviceLeft: {
    flex: 1,
  },
  serviceName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
  },
  serviceDesc: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 4,
    lineHeight: 18,
  },
  serviceMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 6,
  },
  serviceDuration: {
    marginLeft: 4,
    fontSize: 12,
    color: '#9CA3AF',
  },
  serviceRight: {
    alignItems: 'flex-end',
    justifyContent: 'center',
    marginLeft: 12,
  },
  servicePrice: {
    fontSize: 18,
    fontWeight: '800',
    color: '#BE185D',
  },
  galleryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  galleryImage: {
    width: GALLERY_IMAGE_SIZE,
    height: GALLERY_IMAGE_SIZE,
    borderRadius: 10,
    backgroundColor: '#FCE7F3',
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  detailText: {
    marginLeft: 10,
    fontSize: 14,
    color: '#4B5563',
  },
  placeholderText: {
    fontSize: 14,
    color: '#9CA3AF',
    fontStyle: 'italic',
  },
  bottomSpacer: {
    height: 100,
  },
  bookingBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: '#FCE7F3',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 8,
  },
  bookingBarLeft: {
    flex: 1,
  },
  selectedServiceName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  selectedServicePrice: {
    fontSize: 18,
    fontWeight: '800',
    color: '#BE185D',
  },
  selectPrompt: {
    fontSize: 14,
    color: '#9CA3AF',
  },
  bookButton: {
    paddingHorizontal: 28,
  },
});
