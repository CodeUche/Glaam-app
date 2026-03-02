package com.glamconnect.app.data

import com.google.gson.annotations.SerializedName

// ── Auth ─────────────────────────────────────────────────────────────────────

data class LoginRequest(
    val email: String,
    val password: String
)

data class TokenResponse(
    val access: String,
    val refresh: String
)

// Server login response: { "tokens": { "access": "...", "refresh": "..." }, "user": {...} }
data class LoginResponse(
    val tokens: TokenResponse,
    val user: User?
)

data class RegisterRequest(
    val email: String,
    val password: String,
    @SerializedName("password_confirm") val passwordConfirm: String,
    @SerializedName("first_name") val firstName: String,
    @SerializedName("last_name") val lastName: String,
    val role: String
)

data class RegisterResponse(
    val user: User,
    val tokens: RegisterTokens,
    val message: String?
)

data class RegisterTokens(
    val access: String,
    val refresh: String
)

// ── User ─────────────────────────────────────────────────────────────────────

data class User(
    val id: String,
    val email: String,
    @SerializedName("first_name") val firstName: String,
    @SerializedName("last_name") val lastName: String,
    val role: String
) {
    fun fullName(): String = "$firstName $lastName".trim().ifEmpty { email }
}

data class MeResponse(
    val id: String,
    val email: String,
    @SerializedName("first_name") val firstName: String,
    @SerializedName("last_name") val lastName: String,
    val role: String
) {
    fun toUser() = User(id, email, firstName, lastName, role)
    fun fullName(): String = "$firstName $lastName".trim().ifEmpty { email }
}

// ── Artist profile ────────────────────────────────────────────────────────────

data class ArtistProfile(
    val id: String,
    val user: User,
    val bio: String?,
    @SerializedName("hourly_rate") val hourlyRate: String,
    val location: String?,
    @SerializedName("is_available") val isAvailable: Boolean,
    val specialties: List<String>?,
    @SerializedName("average_rating") val averageRating: Double?,
    @SerializedName("total_reviews") val totalReviews: Int?
)

// ── Service ───────────────────────────────────────────────────────────────────

data class Service(
    val id: String,
    val name: String,
    val description: String?,
    val price: String,
    val duration: Int,
    val category: String,
    @SerializedName("is_active") val isActive: Boolean
)

// ── Booking ───────────────────────────────────────────────────────────────────

data class Booking(
    val id: String,
    val client: User?,
    val service: Service?,
    val status: String,
    @SerializedName("booking_date") val bookingDate: String?,
    @SerializedName("start_time") val startTime: String?,
    @SerializedName("created_at") val createdAt: String?,
    val notes: String?,
    @SerializedName("artist_name") val artistName: String?
)

data class BookingCreateRequest(
    val artist: String,
    val service: String,
    @SerializedName("booking_date") val bookingDate: String,
    @SerializedName("start_time") val startTime: String,
    @SerializedName("end_time") val endTime: String,
    val location: String = "",
    @SerializedName("client_notes") val clientNotes: String = ""
)

// ── Paginated list wrapper ────────────────────────────────────────────────────

data class PagedResponse<T>(
    val count: Int,
    val results: List<T>
)
