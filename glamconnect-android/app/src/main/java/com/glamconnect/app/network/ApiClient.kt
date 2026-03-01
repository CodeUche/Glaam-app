package com.glamconnect.app.network

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {

    private var _service: ApiService? = null
    private var _baseUrl: String = ""

    /**
     * Returns the ApiService for the given base URL.
     * Recreates the Retrofit instance if the URL changed.
     */
    fun get(baseUrl: String): ApiService {
        val normalised = baseUrl.trimEnd('/') + "/"
        if (_service == null || normalised != _baseUrl) {
            _baseUrl = normalised
            _service = buildRetrofit(normalised).create(ApiService::class.java)
        }
        return _service!!
    }

    private fun buildRetrofit(baseUrl: String): Retrofit {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }

        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()

        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
}
