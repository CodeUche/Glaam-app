import React from 'react';
import { View, ActivityIndicator, Text, StyleSheet, Modal } from 'react-native';

interface LoadingSpinnerProps {
  visible?: boolean;
  message?: string;
  overlay?: boolean;
}

export default function LoadingSpinner({
  visible = true,
  message = 'Loading...',
  overlay = false,
}: LoadingSpinnerProps) {
  if (!visible) return null;

  const content = (
    <View style={[styles.container, overlay && styles.overlay]}>
      <View style={styles.spinnerBox}>
        <ActivityIndicator size="large" color="#BE185D" />
        {message && <Text style={styles.message}>{message}</Text>}
      </View>
    </View>
  );

  if (overlay) {
    return (
      <Modal transparent animationType="fade" visible={visible}>
        {content}
      </Modal>
    );
  }

  return content;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  overlay: {
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
  },
  spinnerBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 30,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  message: {
    marginTop: 14,
    fontSize: 15,
    color: '#6B7280',
    fontWeight: '500',
  },
});
