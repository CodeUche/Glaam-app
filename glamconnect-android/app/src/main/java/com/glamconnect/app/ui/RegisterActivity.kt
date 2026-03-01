package com.glamconnect.app.ui

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.RadioButton
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.glamconnect.app.MainActivity
import com.glamconnect.app.data.RegisterRequest
import com.glamconnect.app.data.SessionManager
import com.glamconnect.app.databinding.ActivityRegisterBinding
import com.glamconnect.app.network.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class RegisterActivity : AppCompatActivity() {

    private lateinit var binding: ActivityRegisterBinding
    private lateinit var session: SessionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRegisterBinding.inflate(layoutInflater)
        setContentView(binding.root)

        session = SessionManager(this)

        binding.backButton.setOnClickListener { finish() }
        binding.registerButton.setOnClickListener { attemptRegister() }
    }

    private fun attemptRegister() {
        val firstName = binding.firstNameInput.text.toString().trim()
        val lastName  = binding.lastNameInput.text.toString().trim()
        val email     = binding.emailInput.text.toString().trim()
        val password  = binding.passwordInput.text.toString()
        val password2 = binding.confirmPasswordInput.text.toString()

        val role = when (binding.roleGroup.checkedRadioButtonId) {
            binding.roleArtist.id -> "artist"
            else -> "client"
        }

        if (firstName.isEmpty()) { binding.firstNameInput.error = "Required"; return }
        if (lastName.isEmpty())  { binding.lastNameInput.error = "Required"; return }
        if (email.isEmpty() || !email.contains('@')) { binding.emailInput.error = "Enter a valid email"; return }
        if (password.length < 8) { binding.passwordInput.error = "At least 8 characters"; return }
        if (password != password2) { binding.confirmPasswordInput.error = "Passwords don't match"; return }

        setLoading(true)

        lifecycleScope.launch {
            val result = withContext(Dispatchers.IO) {
                try {
                    ApiClient.get(session.serverUrl).register(
                        RegisterRequest(
                            email = email,
                            password = password,
                            passwordConfirm = password2,
                            firstName = firstName,
                            lastName = lastName,
                            role = role
                        )
                    )
                } catch (e: Exception) {
                    null
                }
            }

            setLoading(false)

            when {
                result == null ->
                    showError("Cannot reach server. Check your connection.")

                result.isSuccessful && result.body() != null -> {
                    val body = result.body()!!
                    // Save tokens from registration response
                    session.accessToken  = body.tokens.access
                    session.refreshToken = body.tokens.refresh
                    session.saveUser(body.user)
                    goToMain()
                }

                result.code() == 400 -> {
                    val errBody = result.errorBody()?.string() ?: ""
                    showError(when {
                        errBody.contains("email") && errBody.contains("exist") ->
                            "An account with this email already exists."
                        errBody.contains("password") ->
                            "Password too weak. Use letters, numbers, and symbols."
                        else ->
                            "Registration failed. Please check your details."
                    })
                }

                else ->
                    showError("Registration failed (code ${result.code()}). Try again.")
            }
        }
    }

    private fun setLoading(on: Boolean) {
        binding.registerButton.isEnabled = !on
        binding.progressBar.visibility = if (on) View.VISIBLE else View.GONE
        binding.errorText.visibility = View.GONE
    }

    private fun showError(msg: String) {
        binding.errorText.text = msg
        binding.errorText.visibility = View.VISIBLE
    }

    private fun goToMain() {
        startActivity(Intent(this, MainActivity::class.java))
        finishAffinity()
    }
}
