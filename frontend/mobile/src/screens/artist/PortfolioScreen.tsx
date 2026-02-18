import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  Image,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { api } from '../../lib/api';

const COLORS = {
  primary: '#E11D48',
  white: '#FFFFFF',
  gray: '#6B7280',
  lightGray: '#F3F4F6',
  dark: '#111827',
};

const { width } = Dimensions.get('window');
const IMAGE_SIZE = (width - 48) / 3;

interface PortfolioImage {
  id: string;
  image_url: string;
  thumbnail_url: string;
  caption: string;
  category: string;
  is_featured: boolean;
}

export default function PortfolioScreen({ navigation }: any) {
  const [images, setImages] = useState<PortfolioImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchImages = useCallback(async () => {
    try {
      const response = await api.get('/artists/portfolio/');
      setImages(response.data.results || response.data);
    } catch (error) {
      console.error('Failed to fetch portfolio:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchImages();
  }, [fetchImages]);

  const handleUpload = async () => {
    // In a real app, use react-native-image-picker
    try {
      const { launchImageLibrary } = require('react-native-image-picker');
      launchImageLibrary(
        { mediaType: 'photo', quality: 0.8, maxWidth: 1200, maxHeight: 1200 },
        async (response: any) => {
          if (response.didCancel || response.errorCode) return;

          const asset = response.assets?.[0];
          if (!asset) return;

          const formData = new FormData();
          formData.append('image_url', {
            uri: asset.uri,
            type: asset.type || 'image/jpeg',
            name: asset.fileName || 'photo.jpg',
          } as any);
          formData.append('category', 'other');

          try {
            await api.post('/artists/portfolio/', formData, {
              headers: { 'Content-Type': 'multipart/form-data' },
            });
            fetchImages();
          } catch (err) {
            Alert.alert('Error', 'Failed to upload image');
          }
        }
      );
    } catch (error) {
      Alert.alert('Info', 'Image picker not available in this environment');
    }
  };

  const handleDelete = (imageId: string) => {
    Alert.alert(
      'Delete Image',
      'Are you sure you want to remove this image from your portfolio?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/artists/portfolio/${imageId}/`);
              setImages((prev) => prev.filter((img) => img.id !== imageId));
            } catch (error) {
              Alert.alert('Error', 'Failed to delete image');
            }
          },
        },
      ]
    );
  };

  const renderImage = ({ item }: { item: PortfolioImage }) => (
    <TouchableOpacity
      style={styles.imageContainer}
      onLongPress={() => handleDelete(item.id)}
    >
      <Image
        source={{ uri: item.thumbnail_url || item.image_url }}
        style={styles.image}
        resizeMode="cover"
      />
      {item.is_featured && (
        <View style={styles.featuredBadge}>
          <Text style={styles.featuredText}>Featured</Text>
        </View>
      )}
      {item.category !== 'other' && (
        <View style={styles.categoryBadge}>
          <Text style={styles.categoryText}>{item.category}</Text>
        </View>
      )}
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Portfolio</Text>
        <TouchableOpacity style={styles.uploadBtn} onPress={handleUpload}>
          <Text style={styles.uploadBtnText}>+ Upload</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.subtitle}>
        {images.length} image{images.length !== 1 ? 's' : ''} - Long press to delete
      </Text>

      {/* Grid */}
      <FlatList
        data={images}
        keyExtractor={(item) => item.id}
        renderItem={renderImage}
        numColumns={3}
        columnWrapperStyle={styles.row}
        contentContainerStyle={styles.grid}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchImages(); }} />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyTitle}>No portfolio images yet</Text>
            <Text style={styles.emptyText}>
              Upload your best work to attract clients
            </Text>
            <TouchableOpacity style={styles.emptyUploadBtn} onPress={handleUpload}>
              <Text style={styles.uploadBtnText}>Upload Your First Image</Text>
            </TouchableOpacity>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.lightGray },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  title: { fontSize: 24, fontWeight: '700', color: COLORS.dark },
  subtitle: { fontSize: 13, color: COLORS.gray, paddingHorizontal: 16, marginTop: 4, marginBottom: 12 },
  uploadBtn: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  uploadBtnText: { color: COLORS.white, fontWeight: '600', fontSize: 14 },
  grid: { paddingHorizontal: 12 },
  row: { gap: 4, marginBottom: 4 },
  imageContainer: { width: IMAGE_SIZE, height: IMAGE_SIZE, borderRadius: 8, overflow: 'hidden' },
  image: { width: '100%', height: '100%' },
  featuredBadge: {
    position: 'absolute',
    top: 4,
    left: 4,
    backgroundColor: COLORS.primary,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  featuredText: { color: COLORS.white, fontSize: 10, fontWeight: '600' },
  categoryBadge: {
    position: 'absolute',
    bottom: 4,
    left: 4,
    backgroundColor: 'rgba(0,0,0,0.6)',
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  categoryText: { color: COLORS.white, fontSize: 10 },
  empty: { paddingVertical: 60, alignItems: 'center', paddingHorizontal: 32 },
  emptyTitle: { fontSize: 18, fontWeight: '600', color: COLORS.dark, marginBottom: 8 },
  emptyText: { fontSize: 14, color: COLORS.gray, textAlign: 'center', marginBottom: 20 },
  emptyUploadBtn: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
});
