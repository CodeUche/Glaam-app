package com.glamconnect.app.ui

import android.content.Intent
import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.glamconnect.app.MainActivity
import com.glamconnect.app.SetupActivity
import com.glamconnect.app.data.LoginRequest
import com.glamconnect.app.data.SessionManager
import com.glamconnect.app.databinding.ActivityLoginBinding
import com.glamconnect.app.network.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class LoginActivity : AppCompatActivity() {

    private lateinit var binding: ActivityLoginBinding
    private lateinit var session: SessionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        session = SessionManager(this)

        if (session.isLoggedIn) {
            goToMain()
            return
        }

        binding.signInButton.setOnClickListener { attemptLogin() }

        binding.createAccountText.setOnClickListener {
            startActivity(Intent(this, RegisterActivity::class.java))
        }

        binding.changeServerText.setOnClickListener {
            startActivity(Intent(this, SetupActivity::class.java))
        }
    }

    private fun attemptLogin() {
        val email = binding.emailInput.text.toString().trim()
        val password = binding.passwordInput.text.toString()

        if (email.isEmpty()) { binding.emailInput.error = "Required"; return }
        if (password.isEmpty()) { binding.passwordInput.error = "Required"; return }

        setLoading(true)

        lifecycleScope.launch {
            val loginResult = withContext(Dispatchers.IO) {
                try {
                    ApiClient.get(session.serverUrl).login(LoginRequest(email, password))
                } catch (e: Exception) {
                    null
                }
            }

            setLoading(false)

            when {
                loginResult == null ->
                    showError("Cannot reach server. Check your connection.")
                loginResult.code() == 400 || loginResult.code() == 401 ->
                    showError("Incorrect email or password.")
                loginResult.isSuccessful && loginResult.body() != null -> {
                    session.saveTokens(loginResult.body()!!)
                    fetchUserRoleThenGo()
                }
                else ->
                    showError("Login failed (code ${loginResult.code()}). Try again.")
            }
        }
    }

    private fun fetchUserRoleThenGo() {
        lifecycleScope.launch {
            val meResult = withContext(Dispatchers.IO) {
                try {
                    ApiClient.get(session.serverUrl).getMe(session.authHeader)
                } catch (e: Exception) {
                    null
                }
            }
            if (meResult?.isSuccessful == true) {
                meResult.body()?.let { session.saveUser(it.toUser()) }
            }
            goToMain()
        }
    }

    private fun setLoading(on: Boolean) {
        binding.signInButton.isEnabled = !on
        binding.progressBar.visibility = if (on) View.VISIBLE else View.GONE
        binding.errorText.visibility = View.GONE
    }

    private fun showError(msg: String) {
        binding.errorText.text = msg
        binding.errorText.visibility = View.VISIBLE
    }

    private fun goToMain() {
        startActivity(Intent(this, MainActivity::class.java))
        finish()
    }
}
