// ============================================================
// GlamConnect Type Definitions
// ============================================================

export type UserRole = 'client' | 'artist';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  phone: string;
  avatar: string | null;
  is_verified: boolean;
  date_joined: string;
  location: string;
}

export interface ArtistProfile {
  id: number;
  user: User;
  bio: string;
  specialties: string[];
  years_of_experience: number;
  hourly_rate: number;
  portfolio_images: PortfolioImage[];
  services: Service[];
  average_rating: number;
  total_reviews: number;
  total_bookings: number;
  is_available: boolean;
  travel_radius_km: number;
  latitude: number | null;
  longitude: number | null;
  instagram_handle: string;
  certifications: string[];
  created_at: string;
  updated_at: string;
}

export interface PortfolioImage {
  id: number;
  image: string;
  caption: string;
  order: number;
  created_at: string;
}

export interface Service {
  id: number;
  artist: number;
  name: string;
  description: string;
  price: number;
  duration_minutes: number;
  category: ServiceCategory;
  is_active: boolean;
}

export type ServiceCategory =
  | 'bridal'
  | 'editorial'
  | 'everyday'
  | 'special_event'
  | 'sfx'
  | 'theatrical'
  | 'lessons';

export type BookingStatus =
  | 'pending'
  | 'confirmed'
  | 'in_progress'
  | 'completed'
  | 'cancelled'
  | 'rejected';

export interface Booking {
  id: number;
  client: User;
  artist: ArtistProfile;
  service: Service;
  status: BookingStatus;
  booking_date: string;
  booking_time: string;
  location: string;
  notes: string;
  total_price: number;
  created_at: string;
  updated_at: string;
  review: Review | null;
}

export interface Review {
  id: number;
  booking: number;
  client: User;
  artist: number;
  rating: number;
  comment: string;
  images: string[];
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: number;
  user: number;
  type: NotificationType;
  title: string;
  message: string;
  data: Record<string, unknown>;
  is_read: boolean;
  created_at: string;
}

export type NotificationType =
  | 'booking_request'
  | 'booking_confirmed'
  | 'booking_cancelled'
  | 'booking_completed'
  | 'booking_rejected'
  | 'new_review'
  | 'new_message'
  | 'payment_received'
  | 'system';

// ---------- Auth ----------
export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone: string;
  role: UserRole;
}

// ---------- API Responses ----------
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ArtistSearchParams {
  query?: string;
  category?: ServiceCategory;
  min_price?: number;
  max_price?: number;
  min_rating?: number;
  latitude?: number;
  longitude?: number;
  radius_km?: number;
  page?: number;
}

export interface DashboardStats {
  total_earnings: number;
  monthly_earnings: number;
  total_bookings: number;
  pending_bookings: number;
  completed_bookings: number;
  average_rating: number;
  total_reviews: number;
}

// ---------- Navigation ----------
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
};

export type ClientTabParamList = {
  Home: undefined;
  Bookings: undefined;
  Favorites: undefined;
  Profile: undefined;
};

export type ArtistTabParamList = {
  Dashboard: undefined;
  ManageBookings: undefined;
  Portfolio: undefined;
  Profile: undefined;
};

export type RootStackParamList = {
  Auth: undefined;
  ClientMain: undefined;
  ArtistMain: undefined;
  ArtistDetail: { artistId: number };
  BookingDetail: { bookingId: number };
};
