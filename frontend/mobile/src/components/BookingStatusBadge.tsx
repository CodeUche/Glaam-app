import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { BookingStatus } from '../types';

interface BookingStatusBadgeProps {
  status: BookingStatus;
}

const STATUS_CONFIG: Record<
  BookingStatus,
  { label: string; backgroundColor: string; textColor: string }
> = {
  pending: {
    label: 'Pending',
    backgroundColor: '#FEF3C7',
    textColor: '#92400E',
  },
  confirmed: {
    label: 'Confirmed',
    backgroundColor: '#DBEAFE',
    textColor: '#1E40AF',
  },
  in_progress: {
    label: 'In Progress',
    backgroundColor: '#E0E7FF',
    textColor: '#3730A3',
  },
  completed: {
    label: 'Completed',
    backgroundColor: '#D1FAE5',
    textColor: '#065F46',
  },
  cancelled: {
    label: 'Cancelled',
    backgroundColor: '#FEE2E2',
    textColor: '#991B1B',
  },
  rejected: {
    label: 'Rejected',
    backgroundColor: '#F3E8FF',
    textColor: '#6B21A8',
  },
};

export default function BookingStatusBadge({
  status,
}: BookingStatusBadgeProps) {
  const config = STATUS_CONFIG[status];

  return (
    <View
      style={[styles.badge, { backgroundColor: config.backgroundColor }]}
    >
      <Text style={[styles.text, { color: config.textColor }]}>
        {config.label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: 12,
    fontWeight: '700',
  },
});
