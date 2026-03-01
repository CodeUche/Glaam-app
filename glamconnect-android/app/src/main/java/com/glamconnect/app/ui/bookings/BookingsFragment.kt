package com.glamconnect.app.ui.bookings

import android.app.AlertDialog
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.glamconnect.app.data.Booking
import com.glamconnect.app.data.SessionManager
import com.glamconnect.app.databinding.FragmentBookingsBinding
import com.glamconnect.app.network.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class BookingsFragment : Fragment() {

    private var _binding: FragmentBookingsBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentBookingsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.recyclerView.layoutManager = LinearLayoutManager(requireContext())
        loadBookings()
        binding.retryButton.setOnClickListener { loadBookings() }
    }

    private fun loadBookings() {
        val session = SessionManager(requireContext())
        setLoadingState()

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val resp = withContext(Dispatchers.IO) {
                    ApiClient.get(session.serverUrl).getBookings(session.authHeader)
                }

                withContext(Dispatchers.Main) {
                    if (resp.isSuccessful) {
                        val bookings  = resp.body()?.results ?: emptyList()
                        val isClient  = session.isClient
                        val isEmpty   = bookings.isEmpty()

                        binding.recyclerView.adapter = BookingsAdapter(
                            bookings     = bookings,
                            isClientView = isClient,
                            onCancel     = if (isClient) ::confirmCancel else null
                        )

                        binding.progressBar.visibility  = View.GONE
                        binding.errorGroup.visibility   = View.GONE
                        binding.recyclerView.visibility = if (isEmpty) View.GONE else View.VISIBLE
                        binding.emptyText.text = if (isClient)
                            "You have no bookings yet."
                        else
                            "No incoming bookings yet."
                        binding.emptyText.visibility = if (isEmpty) View.VISIBLE else View.GONE

                    } else {
                        showError("Could not load bookings (${resp.code()})")
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) { showError("Connection error: ${e.message}") }
            }
        }
    }

    private fun confirmCancel(booking: Booking) {
        AlertDialog.Builder(requireContext())
            .setTitle("Cancel Booking")
            .setMessage("Cancel your booking for ${booking.service?.name ?: "this service"}?")
            .setPositiveButton("Yes, Cancel") { _, _ -> cancelBooking(booking) }
            .setNegativeButton("Keep", null)
            .show()
    }

    private fun cancelBooking(booking: Booking) {
        val session = SessionManager(requireContext())
        setLoadingState()

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val resp = withContext(Dispatchers.IO) {
                    ApiClient.get(session.serverUrl)
                        .cancelBooking(session.authHeader, booking.id)
                }
                withContext(Dispatchers.Main) {
                    if (resp.isSuccessful) {
                        loadBookings()
                    } else {
                        showError("Could not cancel booking (${resp.code()})")
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) { showError("Connection error: ${e.message}") }
            }
        }
    }

    private fun setLoadingState() {
        binding.progressBar.visibility  = View.VISIBLE
        binding.recyclerView.visibility = View.GONE
        binding.errorGroup.visibility   = View.GONE
        binding.emptyText.visibility    = View.GONE
    }

    private fun showError(msg: String) {
        binding.progressBar.visibility  = View.GONE
        binding.recyclerView.visibility = View.GONE
        binding.errorGroup.visibility   = View.VISIBLE
        binding.emptyText.visibility    = View.GONE
        binding.errorText.text = msg
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
