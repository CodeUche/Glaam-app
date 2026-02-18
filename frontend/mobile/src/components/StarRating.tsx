import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface StarRatingProps {
  rating: number;
  maxStars?: number;
  size?: number;
  color?: string;
  interactive?: boolean;
  onRatingChange?: (rating: number) => void;
}

export default function StarRating({
  rating,
  maxStars = 5,
  size = 20,
  color = '#F59E0B',
  interactive = false,
  onRatingChange,
}: StarRatingProps) {
  const renderStar = (index: number) => {
    const starNumber = index + 1;
    let iconName: keyof typeof Ionicons.glyphMap;

    if (rating >= starNumber) {
      iconName = 'star';
    } else if (rating >= starNumber - 0.5) {
      iconName = 'star-half';
    } else {
      iconName = 'star-outline';
    }

    const star = (
      <Ionicons
        name={iconName}
        size={size}
        color={color}
        style={styles.star}
      />
    );

    if (interactive && onRatingChange) {
      return (
        <TouchableOpacity
          key={index}
          onPress={() => onRatingChange(starNumber)}
          activeOpacity={0.6}
        >
          {star}
        </TouchableOpacity>
      );
    }

    return <View key={index}>{star}</View>;
  };

  return (
    <View style={styles.container}>
      {Array.from({ length: maxStars }, (_, i) => renderStar(i))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  star: {
    marginRight: 2,
  },
});
