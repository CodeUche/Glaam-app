import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import {
  AuthStackParamList,
  ClientTabParamList,
  RootStackParamList,
} from '../types';
import { useAuthStore } from '../lib/auth';

// Auth screens
import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';

// Client screens
import HomeScreen from '../screens/client/HomeScreen';
import BookingsScreen from '../screens/client/BookingsScreen';
import BookingDetailScreen from '../screens/client/BookingDetailScreen';
import FavoritesScreen from '../screens/client/FavoritesScreen';
import ArtistDetailScreen from '../screens/client/ArtistDetailScreen';

// Common screens
import ProfileScreen from '../screens/common/ProfileScreen';

// Artist navigator
import ArtistNavigator from './ArtistNavigator';

const Stack = createStackNavigator<RootStackParamList>();
const AuthStack = createStackNavigator<AuthStackParamList>();
const ClientTab = createBottomTabNavigator<ClientTabParamList>();

// ---------- Auth Stack ----------
function AuthNavigator() {
  return (
    <AuthStack.Navigator
      screenOptions={{
        headerShown: false,
        cardStyle: { backgroundColor: '#FFF1F2' },
      }}
    >
      <AuthStack.Screen name="Login" component={LoginScreen} />
      <AuthStack.Screen name="Register" component={RegisterScreen} />
    </AuthStack.Navigator>
  );
}

// ---------- Client Tabs ----------
function ClientTabNavigator() {
  return (
    <ClientTab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap = 'home';
          switch (route.name) {
            case 'Home':
              iconName = focused ? 'home' : 'home-outline';
              break;
            case 'Bookings':
              iconName = focused ? 'calendar' : 'calendar-outline';
              break;
            case 'Favorites':
              iconName = focused ? 'heart' : 'heart-outline';
              break;
            case 'Profile':
              iconName = focused ? 'person' : 'person-outline';
              break;
          }
          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#BE185D',
        tabBarInactiveTintColor: '#9CA3AF',
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopColor: '#FCE7F3',
          borderTopWidth: 1,
          paddingBottom: 5,
          paddingTop: 5,
          height: 60,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '600',
        },
        headerStyle: {
          backgroundColor: '#BE185D',
          elevation: 0,
          shadowOpacity: 0,
        },
        headerTintColor: '#FFFFFF',
        headerTitleStyle: {
          fontWeight: '700',
          fontSize: 18,
        },
      })}
    >
      <ClientTab.Screen
        name="Home"
        component={HomeScreen}
        options={{ title: 'Discover' }}
      />
      <ClientTab.Screen
        name="Bookings"
        component={BookingsScreen}
        options={{ title: 'My Bookings' }}
      />
      <ClientTab.Screen
        name="Favorites"
        component={FavoritesScreen}
        options={{ title: 'Favorites' }}
      />
      <ClientTab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ title: 'Profile' }}
      />
    </ClientTab.Navigator>
  );
}

// ---------- Root Navigator ----------
export default function AppNavigator() {
  const { isAuthenticated, user } = useAuthStore();

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {!isAuthenticated ? (
        <Stack.Screen name="Auth" component={AuthNavigator} />
      ) : user?.role === 'artist' ? (
        <Stack.Screen name="ArtistMain" component={ArtistNavigator} />
      ) : (
        <>
          <Stack.Screen name="ClientMain" component={ClientTabNavigator} />
          <Stack.Screen
            name="ArtistDetail"
            component={ArtistDetailScreen}
            options={{
              headerShown: true,
              headerStyle: { backgroundColor: '#BE185D' },
              headerTintColor: '#FFFFFF',
              headerTitle: 'Artist Profile',
            }}
          />
          <Stack.Screen
            name="BookingDetail"
            component={BookingDetailScreen}
            options={{
              headerShown: true,
              headerStyle: { backgroundColor: '#BE185D' },
              headerTintColor: '#FFFFFF',
              headerTitle: 'Booking Details',
            }}
          />
        </>
      )}
    </Stack.Navigator>
  );
}
