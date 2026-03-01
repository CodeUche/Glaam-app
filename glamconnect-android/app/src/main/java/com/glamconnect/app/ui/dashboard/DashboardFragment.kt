package com.glamconnect.app.ui.dashboard

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.glamconnect.app.data.SessionManager
import com.glamconnect.app.databinding.FragmentDashboardBinding
import com.glamconnect.app.network.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class DashboardFragment : Fragment() {

    private var _binding: FragmentDashboardBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentDashboardBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        loadStats()
        binding.retryButton.setOnClickListener { loadStats() }
    }

    private fun loadStats() {
        val session = SessionManager(requireContext())
        showLoading(true)

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val api  = ApiClient.get(session.serverUrl)
                val auth = session.authHeader

                if (session.isAdmin) {
                    // Admin: load both bookings and artists count in parallel
                    val bookingsD = async(Dispatchers.IO) { api.getBookings(auth) }
                    val artistsD  = async(Dispatchers.IO) { api.getArtists(auth) }
                    val bookingsResp = bookingsD.await()
                    val artistsResp  = artistsD.await()

                    if (bookingsResp.isSuccessful && artistsResp.isSuccessful) {
                        val bookings = bookingsResp.body()
                        val artists  = artistsResp.body()
                        binding.headerSubtitle.text    = "Platform overview"
                        binding.statTotalBookings.text = (bookings?.count ?: 0).toString()
                        binding.statPending.text       = (bookings?.results?.count { it.status == "pending" } ?: 0).toString()
                        binding.statConfirmed.text     = (bookings?.results?.count { it.status == "confirmed" } ?: 0).toString()
                        binding.statArtists.text       = (artists?.count ?: 0).toString()
                        binding.labelStat4.text        = "Artists"
                        showLoading(false)
                    } else {
                        showError("Could not load data (${bookingsResp.code()})")
                    }
                } else {
                    // Client or Artist: load bookings only (backend filters by role)
                    val resp = withContext(Dispatchers.IO) { api.getBookings(auth) }
                    if (resp.isSuccessful) {
                        val bookings = resp.body()?.results ?: emptyList()
                        val firstName = session.userName.ifEmpty { "" }.split(" ").first().ifEmpty { "there" }
                        binding.headerSubtitle.text    = "Welcome back, $firstName"
                        binding.statTotalBookings.text = bookings.size.toString()
                        binding.statPending.text       = bookings.count { it.status == "pending" }.toString()
                        binding.statConfirmed.text     = bookings.count { it.status == "confirmed" }.toString()
                        binding.statArtists.text       = bookings.count { it.status == "completed" }.toString()
                        binding.labelStat4.text        = "Completed"
                        showLoading(false)
                    } else {
                        showError("Could not load data (${resp.code()})")
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) { showError("Connection error: ${e.message}") }
            }
        }
    }

    private fun showLoading(on: Boolean) {
        binding.progressBar.visibility = if (on) View.VISIBLE else View.GONE
        binding.statsGrid.visibility   = if (on) View.GONE   else View.VISIBLE
        binding.errorGroup.visibility  = View.GONE
    }

    private fun showError(msg: String) {
        binding.progressBar.visibility = View.GONE
        binding.statsGrid.visibility   = View.GONE
        binding.errorGroup.visibility  = View.VISIBLE
        binding.errorText.text = msg
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
