package com.glamconnect.app.ui.settings

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.appcompat.app.AppCompatDelegate
import androidx.fragment.app.Fragment
import com.glamconnect.app.data.SessionManager
import com.glamconnect.app.databinding.FragmentSettingsBinding
import com.glamconnect.app.SetupActivity
import com.glamconnect.app.ui.LoginActivity

class SettingsFragment : Fragment() {

    private var _binding: FragmentSettingsBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSettingsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val session = SessionManager(requireContext())

        // Account info
        binding.userNameText.text  = session.userName.ifEmpty { "User" }
        binding.userEmailText.text = session.userEmail.ifEmpty { "" }
        binding.userRoleText.text  = session.userRole.replaceFirstChar { it.uppercase() }

        // Server URL
        binding.serverUrlText.text = session.serverUrl.ifEmpty { "Not configured" }

        // Dark mode toggle
        binding.darkModeSwitch.isChecked = session.isDarkMode
        binding.darkModeSwitch.setOnCheckedChangeListener { _, isChecked ->
            session.isDarkMode = isChecked
            AppCompatDelegate.setDefaultNightMode(
                if (isChecked) AppCompatDelegate.MODE_NIGHT_YES
                else AppCompatDelegate.MODE_NIGHT_NO
            )
        }

        binding.changeServerButton.setOnClickListener {
            session.logout()
            startActivity(Intent(requireContext(), SetupActivity::class.java))
            requireActivity().finish()
        }

        binding.logoutButton.setOnClickListener {
            session.logout()
            startActivity(Intent(requireContext(), LoginActivity::class.java))
            requireActivity().finish()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
