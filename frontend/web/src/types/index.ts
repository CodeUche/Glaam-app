export type UserRole = "client" | "artist" | "admin";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  avatar: string | null;
  phone: string | null;
  location: string | null;
  is_verified: boolean;
  date_joined: string;
}

export interface ArtistProfile {
  id: string;
  user: User;
  bio: string;
  specialties: string[];
  experience_years: number;
  hourly_rate: number;
  portfolio_images: PortfolioImage[];
  services: Service[];
  average_rating: number;
  total_reviews: number;
  total_bookings: number;
  is_available: boolean;
  travel_radius_km: number;
  instagram_handle: string | null;
  website: string | null;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PortfolioImage {
  id: string;
  image_url: string;
  caption: string | null;
  category: string | null;
  created_at: string;
}

export interface Service {
  id: string;
  artist_id: string;
  name: string;
  description: string;
  price: number;
  duration_minutes: number;
  category: ServiceCategory;
  is_active: boolean;
}

export type ServiceCategory =
  | "bridal"
  | "editorial"
  | "special_occasion"
  | "everyday"
  | "sfx"
  | "theatrical"
  | "lessons"
  | "other";

export type BookingStatus =
  | "pending"
  | "confirmed"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "declined";

export interface Booking {
  id: string;
  client: User;
  artist: ArtistProfile;
  services: Service[];
  status: BookingStatus;
  scheduled_date: string;
  scheduled_time: string;
  location: string;
  notes: string | null;
  total_price: number;
  payment_status: "pending" | "paid" | "refunded";
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  cancelled_at: string | null;
  cancellation_reason: string | null;
}

export interface Review {
  id: string;
  booking_id: string;
  client: User;
  artist_id: string;
  rating: number;
  comment: string;
  artist_response: string | null;
  images: string[];
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  type: NotificationType;
  title: string;
  message: string;
  data: Record<string, unknown> | null;
  is_read: boolean;
  created_at: string;
}

export type NotificationType =
  | "booking_request"
  | "booking_confirmed"
  | "booking_cancelled"
  | "booking_completed"
  | "new_review"
  | "payment_received"
  | "message"
  | "system";

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

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
  role: UserRole;
  phone?: string;
}

export interface ArtistFilters {
  search?: string;
  specialty?: string;
  min_price?: number;
  max_price?: number;
  min_rating?: number;
  location?: string;
  is_available?: boolean;
  ordering?: string;
  page?: number;
}

export interface DashboardStats {
  total_bookings: number;
  pending_bookings: number;
  completed_bookings: number;
  total_earnings: number;
  monthly_earnings: number;
  average_rating: number;
  total_reviews: number;
}
