package com.glamconnect.app.network

import com.glamconnect.app.data.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // ── Auth ─────────────────────────────────────────────────────────────────

    @POST("api/v1/auth/login/")
    suspend fun login(@Body request: LoginRequest): Response<TokenResponse>

    @POST("api/v1/auth/register/")
    suspend fun register(@Body request: RegisterRequest): Response<RegisterResponse>

    @GET("api/v1/auth/me/")
    suspend fun getMe(
        @Header("Authorization") token: String
    ): Response<MeResponse>

    // ── Artist profiles ───────────────────────────────────────────────────────

    @GET("api/v1/artists/")
    suspend fun getArtists(
        @Header("Authorization") token: String
    ): Response<PagedResponse<ArtistProfile>>

    // ── Services ──────────────────────────────────────────────────────────────

    @GET("api/v1/services/")
    suspend fun getServices(
        @Header("Authorization") token: String
    ): Response<PagedResponse<Service>>

    @GET("api/v1/services/")
    suspend fun getArtistServices(
        @Header("Authorization") token: String,
        @Query("artist") artistId: String
    ): Response<PagedResponse<Service>>

    // ── Bookings ──────────────────────────────────────────────────────────────

    @GET("api/v1/bookings/")
    suspend fun getBookings(
        @Header("Authorization") token: String
    ): Response<PagedResponse<Booking>>

    @POST("api/v1/bookings/")
    suspend fun createBooking(
        @Header("Authorization") token: String,
        @Body request: BookingCreateRequest
    ): Response<Booking>

    @POST("api/v1/bookings/{id}/cancel/")
    suspend fun cancelBooking(
        @Header("Authorization") token: String,
        @Path("id") bookingId: String
    ): Response<Booking>

    // ── Dashboard stats helper ────────────────────────────────────────────────

    @GET("api/v1/bookings/?status=pending&page_size=1")
    suspend fun getPendingCount(
        @Header("Authorization") token: String
    ): Response<PagedResponse<Booking>>
}
