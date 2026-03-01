package com.glamconnect.app

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.glamconnect.app.data.SessionManager
import com.glamconnect.app.databinding.ActivitySetupBinding
import com.glamconnect.app.network.ApiClient
import com.glamconnect.app.ui.LoginActivity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * First-launch screen: asks the user to enter the GlamConnect server URL.
 * Tests the connection via Retrofit (no WebView).
 */
class SetupActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySetupBinding
    private lateinit var session: SessionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySetupBinding.inflate(layoutInflater)
        setContentView(binding.root)

        session = SessionManager(this)

        // Auto-skip to login if server URL is already saved
        if (session.isServerConfigured) {
            startActivity(Intent(this, LoginActivity::class.java))
            finish()
            return
        }

        binding.connectButton.setOnClickListener { validateAndConnect() }
    }

    private fun validateAndConnect() {
        val raw = binding.urlInput.text.toString().trim().trimEnd('/')
        if (raw.isEmpty()) {
            binding.urlInput.error = "Please enter the server address"
            return
        }
        if (!raw.startsWith("http://") && !raw.startsWith("https://")) {
            binding.urlInput.error = "Must start with http:// or https://"
            return
        }
        testConnection(raw)
    }

    private fun testConnection(url: String) {
        binding.connectButton.isEnabled = false
        binding.statusText.visibility = View.VISIBLE
        binding.statusText.text = "Testing connection…"

        lifecycleScope.launch {
            val reachable = withContext(Dispatchers.IO) {
                try {
                    val client = ApiClient.get(url)
                    val resp = client.getArtists("invalid_token")
                    resp.code() in 200..499
                } catch (e: Exception) {
                    false
                }
            }

            if (reachable) {
                session.serverUrl = url
                binding.statusText.text = "Connected! ✓"
                startActivity(Intent(this@SetupActivity, LoginActivity::class.java))
                finish()
            } else {
                binding.connectButton.isEnabled = true
                binding.statusText.text =
                    "⚠ Cannot reach server.\n\nMake sure GlamConnect is running on your PC and both devices are on the same WiFi network."
                Toast.makeText(this@SetupActivity, "Cannot connect to $url", Toast.LENGTH_LONG).show()
            }
        }
    }
}
