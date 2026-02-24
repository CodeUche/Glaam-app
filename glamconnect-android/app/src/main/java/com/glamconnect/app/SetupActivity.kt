package com.glamconnect.app

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.glamconnect.app.databinding.ActivitySetupBinding

class SetupActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySetupBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySetupBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Pre-fill with saved URL if one exists
        val prefs = getSharedPreferences("glamconnect", MODE_PRIVATE)
        val saved = prefs.getString("server_url", "")
        if (!saved.isNullOrEmpty()) {
            binding.urlInput.setText(saved)
        }

        binding.connectButton.setOnClickListener {
            val raw = binding.urlInput.text.toString().trim().trimEnd('/')
            if (raw.isEmpty()) {
                binding.urlInput.error = "Please enter the server URL"
                return@setOnClickListener
            }

            // Basic format check
            if (!raw.startsWith("http://") && !raw.startsWith("https://")) {
                binding.urlInput.error = "URL must start with http:// or https://"
                return@setOnClickListener
            }

            testConnection(raw)
        }
    }

    private fun testConnection(url: String) {
        binding.connectButton.isEnabled = false
        binding.statusText.visibility = View.VISIBLE
        binding.statusText.text = "Testing connection to server…"

        // Use a hidden WebView to do a quick connectivity test
        val testView = WebView(this)
        testView.settings.javaScriptEnabled = false

        testView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, loadedUrl: String?) {
                runOnUiThread {
                    saveAndContinue(url)
                }
            }

            override fun onReceivedError(
                view: WebView?,
                errorCode: Int,
                description: String?,
                failingUrl: String?
            ) {
                runOnUiThread {
                    binding.connectButton.isEnabled = true
                    binding.statusText.text = "⚠ Could not reach server. Is GlamConnect running on your PC?\n\nMake sure both devices are on the same WiFi."
                    Toast.makeText(this@SetupActivity, "Cannot connect to $url", Toast.LENGTH_LONG).show()
                }
            }
        }

        testView.loadUrl("$url/api/v1/")

        // Timeout after 8 seconds — assume reachable and let MainActivity handle errors
        binding.root.postDelayed({
            if (binding.connectButton.isEnabled.not()) return@postDelayed
            saveAndContinue(url)
        }, 8000)
    }

    private fun saveAndContinue(url: String) {
        getSharedPreferences("glamconnect", MODE_PRIVATE)
            .edit()
            .putString("server_url", url)
            .apply()

        startActivity(Intent(this, MainActivity::class.java))
        finish()
    }
}
