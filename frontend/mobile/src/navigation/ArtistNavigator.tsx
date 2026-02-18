import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { ArtistTabParamList } from '../types';

import DashboardScreen from '../screens/artist/DashboardScreen';
import ManageBookingsScreen from '../screens/artist/ManageBookingsScreen';
import PortfolioScreen from '../screens/artist/PortfolioScreen';
import ProfileScreen from '../screens/common/ProfileScreen';

const ArtistTab = createBottomTabNavigator<ArtistTabParamList>();

export default function ArtistNavigator() {
  return (
    <ArtistTab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap = 'grid';
          switch (route.name) {
            case 'Dashboard':
              iconName = focused ? 'grid' : 'grid-outline';
              break;
            case 'ManageBookings':
              iconName = focused ? 'calendar' : 'calendar-outline';
              break;
            case 'Portfolio':
              iconName = focused ? 'images' : 'images-outline';
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
      <ArtistTab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{ title: 'Dashboard' }}
      />
      <ArtistTab.Screen
        name="ManageBookings"
        component={ManageBookingsScreen}
        options={{ title: 'Bookings' }}
      />
      <ArtistTab.Screen
        name="Portfolio"
        component={PortfolioScreen}
        options={{ title: 'Portfolio' }}
      />
      <ArtistTab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ title: 'Profile' }}
      />
    </ArtistTab.Navigator>
  );
}
