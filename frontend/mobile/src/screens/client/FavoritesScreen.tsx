import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Image,
  TouchableOpacity,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { RootStackParamList, ArtistProfile, PaginatedResponse } from '../../types';
import StarRating from '../../components/StarRating';
import LoadingSpinner from '../../components/ui/LoadingSpinner';

type FavoritesNav = StackNavigationProp<RootStackParamList>;

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const CARD_WIDTH = (SCREEN_WIDTH - 48 - 12) / 2;

export default function FavoritesScreen() {
  const navigation = useNavigation<FavoritesNav>();

  const {
    data: favorites,
    isLoading,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['favorites'],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<ArtistProfile>>(
        '/favorites/',
      );
      return data;
    },
  });

  const handleArtistPress = (artistId: number) => {
    navigation.navigate('ArtistDetail', { artistId });
  };

  const renderFavoriteItem = ({ item }: { item: ArtistProfile }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => handleArtistPress(item.id)}
      activeOpacity={0.85}
    >
      <Image
        source={
          item.user.avatar
            ? { uri: item.user.avatar }
            : require('../../../assets/default-avatar.png')
        }
        style={styles.cardImage}
      />
      <TouchableOpacity style={styles.heartButton}>
        <Ionicons name="heart" size={18} color="#EF4444" />
      </TouchableOpacity>
      <View style={styles.cardContent}>
        <Text style={styles.cardName} numberOfLines={1}>
          {item.user.full_name}
        </Text>
        <View style={styles.ratingRow}>
          <StarRating rating={item.average_rating} size={12} />
          <Text style={styles.ratingText}>
            {item.average_rating.toFixed(1)}
          </Text>
        </View>
        <Text style={styles.cardPrice}>From ${item.hourly_rate}/hr</Text>
      </View>
    </TouchableOpacity>
  );

  if (isLoading) {
    return <LoadingSpinner message="Loading favorites..." />;
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={favorites?.results ?? []}
        renderItem={renderFavoriteItem}
        keyExtractor={(item) => item.id.toString()}
        numColumns={2}
        columnWrapperStyle={styles.row}
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
        ListHeaderComponent={
          <Text style={styles.headerTitle}>
            {favorites?.count ?? 0} Saved Artist
            {(favorites?.count ?? 0) !== 1 ? 's' : ''}
          </Text>
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="heart-outline" size={56} color="#D1D5DB" />
            <Text style={styles.emptyTitle}>No favorites yet</Text>
            <Text style={styles.emptySubtitle}>
              Tap the heart icon on any artist to save them here
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFF7F8',
  },
  listContent: {
    padding: 16,
    paddingBottom: 24,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 16,
  },
  row: {
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  card: {
    width: CARD_WIDTH,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    overflow: 'hidden',
    shadowColor: '#BE185D',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 3,
  },
  cardImage: {
    width: '100%',
    height: CARD_WIDTH * 1.1,
    backgroundColor: '#FCE7F3',
  },
  heartButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.15,
    shadowRadius: 2,
    elevation: 2,
  },
  cardContent: {
    padding: 10,
  },
  cardName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1F2937',
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  ratingText: {
    marginLeft: 4,
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  cardPrice: {
    fontSize: 13,
    fontWeight: '700',
    color: '#BE185D',
    marginTop: 6,
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
