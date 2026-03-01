package com.glamconnect.app

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.ui.setupWithNavController
import com.glamconnect.app.data.SessionManager
import com.glamconnect.app.databinding.ActivityMainBinding
import androidx.appcompat.app.AppCompatDelegate
import com.glamconnect.app.ui.LoginActivity

/**
 * Main screen — bottom navigation with Dashboard, Artists, Bookings, Settings.
 * No WebView — all screens are native Kotlin UI.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        // Restore dark mode preference before layout inflation
        val session = SessionManager(applicationContext)
        AppCompatDelegate.setDefaultNightMode(
            if (session.isDarkMode) AppCompatDelegate.MODE_NIGHT_YES
            else AppCompatDelegate.MODE_NIGHT_NO
        )

        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        if (!session.isLoggedIn) {
            startActivity(Intent(this, LoginActivity::class.java))
            finish()
            return
        }

        val navHost = supportFragmentManager
            .findFragmentById(R.id.nav_host_fragment) as NavHostFragment
        val navController = navHost.navController

        binding.bottomNavigation.setupWithNavController(navController)
    }
}
