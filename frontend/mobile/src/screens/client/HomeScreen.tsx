import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { Ionicons } from '@expo/vector-icons';
import { RootStackParamList, ServiceCategory, ArtistProfile } from '../../types';
import { useArtists, useArtistSearch } from '../../hooks/useArtists';
import ArtistCard from '../../components/ArtistCard';
import LoadingSpinner from '../../components/ui/LoadingSpinner';

type HomeNav = StackNavigationProp<RootStackParamList>;

const CATEGORIES: { key: ServiceCategory | 'all'; label: string; icon: string }[] = [
  { key: 'all', label: 'All', icon: 'sparkles-outline' },
  { key: 'bridal', label: 'Bridal', icon: 'heart-outline' },
  { key: 'editorial', label: 'Editorial', icon: 'camera-outline' },
  { key: 'everyday', label: 'Everyday', icon: 'sunny-outline' },
  { key: 'special_event', label: 'Events', icon: 'star-outline' },
  { key: 'sfx', label: 'SFX', icon: 'color-wand-outline' },
  { key: 'theatrical', label: 'Theater', icon: 'film-outline' },
  { key: 'lessons', label: 'Lessons', icon: 'school-outline' },
];

export default function HomeScreen() {
  const navigation = useNavigation<HomeNav>();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<
    ServiceCategory | 'all'
  >('all');

  const searchParams = {
    query: searchQuery || undefined,
    category: selectedCategory === 'all' ? undefined : selectedCategory,
  };

  const { data: artists, isLoading, refetch, isRefetching } =
    useArtistSearch(searchParams);

  const handleArtistPress = (artistId: number) => {
    navigation.navigate('ArtistDetail', { artistId });
  };

  const renderArtist = ({ item }: { item: ArtistProfile }) => (
    <ArtistCard
      artist={item}
      onPress={() => handleArtistPress(item.id)}
      onFavoriteToggle={() => {}}
    />
  );

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search-outline" size={20} color="#9CA3AF" />
          <TextInput
            style={styles.searchInput}
            placeholder="Search makeup artists..."
            placeholderTextColor="#9CA3AF"
            value={searchQuery}
            onChangeText={setSearchQuery}
            returnKeyType="search"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={20} color="#9CA3AF" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Category Filters */}
      <View style={styles.categoriesContainer}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoriesContent}
        >
          {CATEGORIES.map((cat) => (
            <TouchableOpacity
              key={cat.key}
              style={[
                styles.categoryChip,
                selectedCategory === cat.key && styles.categoryChipActive,
              ]}
              onPress={() => setSelectedCategory(cat.key)}
            >
              <Ionicons
                name={cat.icon as any}
                size={16}
                color={selectedCategory === cat.key ? '#FFFFFF' : '#BE185D'}
              />
              <Text
                style={[
                  styles.categoryText,
                  selectedCategory === cat.key && styles.categoryTextActive,
                ]}
              >
                {cat.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Artists List */}
      {isLoading ? (
        <LoadingSpinner message="Finding artists..." />
      ) : (
        <FlatList
          data={artists?.results ?? []}
          renderItem={renderArtist}
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
          ListHeaderComponent={
            <View style={styles.listHeader}>
              <Text style={styles.sectionTitle}>
                {selectedCategory === 'all'
                  ? 'Featured Artists'
                  : `${CATEGORIES.find((c) => c.key === selectedCategory)?.label} Artists`}
              </Text>
              <Text style={styles.resultCount}>
                {artists?.count ?? 0} artist{(artists?.count ?? 0) !== 1 ? 's' : ''} found
              </Text>
            </View>
          }
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Ionicons name="search" size={48} color="#D1D5DB" />
              <Text style={styles.emptyTitle}>No artists found</Text>
              <Text style={styles.emptySubtitle}>
                Try adjusting your search or filters
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
  searchContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#BE185D',
    paddingTop: 4,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    paddingHorizontal: 14,
    height: 46,
  },
  searchInput: {
    flex: 1,
    marginLeft: 10,
    fontSize: 15,
    color: '#1F2937',
  },
  categoriesContainer: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#FCE7F3',
  },
  categoriesContent: {
    paddingHorizontal: 12,
    paddingVertical: 12,
    gap: 8,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#FFF1F2',
    marginRight: 4,
  },
  categoryChipActive: {
    backgroundColor: '#BE185D',
  },
  categoryText: {
    marginLeft: 6,
    fontSize: 13,
    fontWeight: '600',
    color: '#BE185D',
  },
  categoryTextActive: {
    color: '#FFFFFF',
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 20,
  },
  listHeader: {
    paddingVertical: 16,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#1F2937',
  },
  resultCount: {
    fontSize: 13,
    color: '#9CA3AF',
    marginTop: 2,
  },
  emptyState: {
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#6B7280',
    marginTop: 12,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#9CA3AF',
    marginTop: 4,
  },
});
