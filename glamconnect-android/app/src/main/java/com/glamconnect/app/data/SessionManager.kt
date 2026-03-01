package com.glamconnect.app.data

import android.content.Context
import android.content.SharedPreferences
import com.glamconnect.app.BuildConfig

/**
 * Persists the server URL, JWT tokens, user info, and preferences across app launches.
 */
class SessionManager(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences("glamconnect_session", Context.MODE_PRIVATE)

    var serverUrl: String
        get() = prefs.getString(KEY_SERVER_URL, BuildConfig.SERVER_URL) ?: BuildConfig.SERVER_URL
        set(value) = prefs.edit().putString(KEY_SERVER_URL, value.trimEnd('/')).apply()

    var accessToken: String
        get() = prefs.getString(KEY_ACCESS_TOKEN, "") ?: ""
        set(value) = prefs.edit().putString(KEY_ACCESS_TOKEN, value).apply()

    var refreshToken: String
        get() = prefs.getString(KEY_REFRESH_TOKEN, "") ?: ""
        set(value) = prefs.edit().putString(KEY_REFRESH_TOKEN, value).apply()

    var userRole: String
        get() = prefs.getString(KEY_USER_ROLE, "client") ?: "client"
        set(value) = prefs.edit().putString(KEY_USER_ROLE, value).apply()

    var userName: String
        get() = prefs.getString(KEY_USER_NAME, "") ?: ""
        set(value) = prefs.edit().putString(KEY_USER_NAME, value).apply()

    var userEmail: String
        get() = prefs.getString(KEY_USER_EMAIL, "") ?: ""
        set(value) = prefs.edit().putString(KEY_USER_EMAIL, value).apply()

    var isDarkMode: Boolean
        get() = prefs.getBoolean(KEY_DARK_MODE, false)
        set(value) = prefs.edit().putBoolean(KEY_DARK_MODE, value).apply()

    val isLoggedIn: Boolean
        get() = accessToken.isNotEmpty()

    val isServerConfigured: Boolean
        get() = serverUrl.isNotEmpty()

    val authHeader: String
        get() = "Bearer $accessToken"

    val isClient: Boolean
        get() = userRole == "client"

    val isArtist: Boolean
        get() = userRole == "artist"

    val isAdmin: Boolean
        get() = userRole == "admin"

    fun saveTokens(response: TokenResponse) {
        accessToken = response.access
        refreshToken = response.refresh
    }

    fun saveUser(user: User) {
        userRole  = user.role
        userName  = user.fullName()
        userEmail = user.email
    }

    fun logout() {
        prefs.edit()
            .remove(KEY_ACCESS_TOKEN)
            .remove(KEY_REFRESH_TOKEN)
            .remove(KEY_USER_ROLE)
            .remove(KEY_USER_NAME)
            .remove(KEY_USER_EMAIL)
            .apply()
    }

    companion object {
        private const val KEY_SERVER_URL   = "server_url"
        private const val KEY_ACCESS_TOKEN = "access_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
        private const val KEY_USER_ROLE    = "user_role"
        private const val KEY_USER_NAME    = "user_name"
        private const val KEY_USER_EMAIL   = "user_email"
        private const val KEY_DARK_MODE    = "dark_mode"
    }
}
