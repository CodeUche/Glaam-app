package com.glamconnect.app.ui.artists

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.glamconnect.app.data.ArtistProfile
import com.glamconnect.app.data.SessionManager
import com.glamconnect.app.databinding.FragmentArtistsBinding
import com.glamconnect.app.network.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class ArtistsFragment : Fragment() {

    private var _binding: FragmentArtistsBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentArtistsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.recyclerView.layoutManager = LinearLayoutManager(requireContext())
        loadArtists()
        binding.retryButton.setOnClickListener { loadArtists() }
    }

    private fun loadArtists() {
        val session = SessionManager(requireContext())
        showLoading(true)

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val resp = withContext(Dispatchers.IO) {
                    ApiClient.get(session.serverUrl).getArtists(session.authHeader)
                }

                if (resp.isSuccessful) {
                    val artists = resp.body()?.results ?: emptyList()
                    val bookHandler = if (session.isClient) ::openBooking else null
                    binding.recyclerView.adapter = ArtistsAdapter(artists, bookHandler)
                    binding.emptyText.visibility = if (artists.isEmpty()) View.VISIBLE else View.GONE
                    showLoading(false)
                } else {
                    showError("Could not load artists (${resp.code()})")
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) { showError("Connection error: ${e.message}") }
            }
        }
    }

    private fun openBooking(artist: ArtistProfile) {
        val intent = Intent(requireContext(), ArtistDetailActivity::class.java)
        intent.putExtra(ArtistDetailActivity.EXTRA_ARTIST_ID, artist.id)
        intent.putExtra(ArtistDetailActivity.EXTRA_ARTIST_NAME, artist.user.fullName())
        intent.putExtra(ArtistDetailActivity.EXTRA_ARTIST_RATE, artist.hourlyRate)
        intent.putExtra(ArtistDetailActivity.EXTRA_ARTIST_LOCATION, artist.location ?: "")
        startActivity(intent)
    }

    private fun showLoading(on: Boolean) {
        binding.progressBar.visibility  = if (on) View.VISIBLE else View.GONE
        binding.recyclerView.visibility = if (on) View.GONE else View.VISIBLE
        binding.errorGroup.visibility   = View.GONE
    }

    private fun showError(msg: String) {
        binding.progressBar.visibility  = View.GONE
        binding.recyclerView.visibility = View.GONE
        binding.errorGroup.visibility   = View.VISIBLE
        binding.errorText.text = msg
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
