import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useForm, Controller } from 'react-hook-form';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { Ionicons } from '@expo/vector-icons';
import Input from '../../components/ui/Input';
import Button from '../../components/ui/Button';
import { useAuthStore } from '../../lib/auth';
import { AuthStackParamList, RegisterData, UserRole } from '../../types';

type RegisterNav = StackNavigationProp<AuthStackParamList, 'Register'>;

export default function RegisterScreen() {
  const navigation = useNavigation<RegisterNav>();
  const { register: registerUser, isLoading } = useAuthStore();
  const [selectedRole, setSelectedRole] = useState<UserRole>('client');

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterData>({
    defaultValues: {
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      phone: '',
      role: 'client',
    },
  });

  const onSubmit = async (data: RegisterData) => {
    try {
      await registerUser({ ...data, role: selectedRole });
    } catch (err: any) {
      Alert.alert('Registration Failed', err.message);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Ionicons name="arrow-back" size={24} color="#BE185D" />
          </TouchableOpacity>
          <Text style={styles.title}>Create Account</Text>
          <Text style={styles.subtitle}>
            Join the GlamConnect community
          </Text>
        </View>

        {/* Role Selection */}
        <View style={styles.roleContainer}>
          <Text style={styles.roleLabel}>I am a:</Text>
          <View style={styles.roleButtons}>
            <TouchableOpacity
              style={[
                styles.roleButton,
                selectedRole === 'client' && styles.roleButtonActive,
              ]}
              onPress={() => setSelectedRole('client')}
            >
              <Ionicons
                name="person-outline"
                size={24}
                color={selectedRole === 'client' ? '#FFFFFF' : '#BE185D'}
              />
              <Text
                style={[
                  styles.roleButtonText,
                  selectedRole === 'client' && styles.roleButtonTextActive,
                ]}
              >
                Client
              </Text>
              <Text
                style={[
                  styles.roleDesc,
                  selectedRole === 'client' && styles.roleDescActive,
                ]}
              >
                Find artists
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.roleButton,
                selectedRole === 'artist' && styles.roleButtonActive,
              ]}
              onPress={() => setSelectedRole('artist')}
            >
              <Ionicons
                name="brush-outline"
                size={24}
                color={selectedRole === 'artist' ? '#FFFFFF' : '#BE185D'}
              />
              <Text
                style={[
                  styles.roleButtonText,
                  selectedRole === 'artist' && styles.roleButtonTextActive,
                ]}
              >
                Artist
              </Text>
              <Text
                style={[
                  styles.roleDesc,
                  selectedRole === 'artist' && styles.roleDescActive,
                ]}
              >
                Offer services
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Form */}
        <View style={styles.form}>
          <View style={styles.nameRow}>
            <View style={styles.nameField}>
              <Controller
                control={control}
                name="first_name"
                rules={{ required: 'First name is required' }}
                render={({ field: { onChange, onBlur, value } }) => (
                  <Input
                    label="First Name"
                    placeholder="Jane"
                    icon="person-outline"
                    value={value}
                    onChangeText={onChange}
                    onBlur={onBlur}
                    error={errors.first_name?.message}
                  />
                )}
              />
            </View>
            <View style={styles.nameField}>
              <Controller
                control={control}
                name="last_name"
                rules={{ required: 'Last name is required' }}
                render={({ field: { onChange, onBlur, value } }) => (
                  <Input
                    label="Last Name"
                    placeholder="Doe"
                    value={value}
                    onChangeText={onChange}
                    onBlur={onBlur}
                    error={errors.last_name?.message}
                  />
                )}
              />
            </View>
          </View>

          <Controller
            control={control}
            name="email"
            rules={{
              required: 'Email is required',
              pattern: {
                value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                message: 'Enter a valid email',
              },
            }}
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="Email"
                placeholder="your@email.com"
                icon="mail-outline"
                keyboardType="email-address"
                autoCapitalize="none"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.email?.message}
              />
            )}
          />

          <Controller
            control={control}
            name="phone"
            rules={{
              required: 'Phone number is required',
            }}
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="Phone"
                placeholder="+1 (555) 000-0000"
                icon="call-outline"
                keyboardType="phone-pad"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.phone?.message}
              />
            )}
          />

          <Controller
            control={control}
            name="password"
            rules={{
              required: 'Password is required',
              minLength: {
                value: 8,
                message: 'Password must be at least 8 characters',
              },
            }}
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="Password"
                placeholder="Create a strong password"
                icon="lock-closed-outline"
                isPassword
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.password?.message}
              />
            )}
          />

          <Button
            title="Create Account"
            onPress={handleSubmit(onSubmit)}
            loading={isLoading}
            style={styles.registerButton}
          />
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>Already have an account? </Text>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Text style={styles.footerLink}>Sign In</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
    backgroundColor: '#FFF1F2',
  },
  container: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingVertical: 30,
  },
  header: {
    marginBottom: 24,
  },
  backButton: {
    marginBottom: 16,
    width: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#1F2937',
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  roleContainer: {
    marginBottom: 24,
  },
  roleLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: '#374151',
    marginBottom: 12,
  },
  roleButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  roleButton: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    paddingVertical: 20,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#FCE7F3',
  },
  roleButtonActive: {
    backgroundColor: '#BE185D',
    borderColor: '#BE185D',
  },
  roleButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#BE185D',
    marginTop: 8,
  },
  roleButtonTextActive: {
    color: '#FFFFFF',
  },
  roleDesc: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
  },
  roleDescActive: {
    color: '#FBD5E5',
  },
  form: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 24,
    shadowColor: '#BE185D',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 6,
  },
  nameRow: {
    flexDirection: 'row',
    gap: 12,
  },
  nameField: {
    flex: 1,
  },
  registerButton: {
    marginTop: 8,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 24,
  },
  footerText: {
    fontSize: 14,
    color: '#6B7280',
  },
  footerLink: {
    fontSize: 14,
    color: '#BE185D',
    fontWeight: '700',
  },
});
