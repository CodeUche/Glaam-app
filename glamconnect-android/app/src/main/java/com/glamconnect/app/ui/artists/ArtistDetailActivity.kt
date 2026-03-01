package com.glamconnect.app.ui.artists

import android.app.DatePickerDialog
import android.app.TimePickerDialog
import android.os.Bundle
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.glamconnect.app.data.BookingCreateRequest
import com.glamconnect.app.data.Service
import com.glamconnect.app.data.SessionManager
import com.glamconnect.app.databinding.ActivityArtistDetailBinding
import com.glamconnect.app.network.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.Calendar

class ArtistDetailActivity : AppCompatActivity() {

    private lateinit var binding: ActivityArtistDetailBinding
    private lateinit var session: SessionManager
    private var services: List<Service> = emptyList()
    private var artistId: String = ""
    private var selectedDate = ""
    private var selectedStartTime = ""
    private var selectedEndTime = ""

    companion object {
        const val EXTRA_ARTIST_ID       = "artist_id"
        const val EXTRA_ARTIST_NAME     = "artist_name"
        const val EXTRA_ARTIST_RATE     = "artist_rate"
        const val EXTRA_ARTIST_LOCATION = "artist_location"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityArtistDetailBinding.inflate(layoutInflater)
        setContentView(binding.root)

        session = SessionManager(this)

        val artistIdExtra = intent.getStringExtra(EXTRA_ARTIST_ID) ?: ""
        val artistName = intent.getStringExtra(EXTRA_ARTIST_NAME) ?: "Artist"
        artistId = artistIdExtra

        binding.artistNameText.text = artistName
        binding.backButton.setOnClickListener { finish() }

        loadServices(artistId)

        binding.dateButton.setOnClickListener { pickDate() }
        binding.timeButton.setOnClickListener { pickTime() }
        binding.bookButton.setOnClickListener { confirmBooking(artistId) }
    }

    private fun loadServices(artistId: String) {
        setLoading(true)
        lifecycleScope.launch {
            val resp = withContext(Dispatchers.IO) {
                try {
                    ApiClient.get(session.serverUrl).getArtistServices(session.authHeader, artistId)
                } catch (e: Exception) { null }
            }

            if (resp?.isSuccessful == true) {
                services = resp.body()?.results ?: emptyList()
                val names = services.map { "${it.name} - $${it.price}" }
                val adapter = ArrayAdapter(this@ArtistDetailActivity, android.R.layout.simple_spinner_item, names)
                adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
                binding.serviceSpinner.adapter = adapter
                setLoading(false)
            } else {
                binding.errorText.visibility = View.VISIBLE
                binding.errorText.text = "Could not load services. Please try again."
                setLoading(false)
            }
        }
    }

    private fun pickDate() {
        val cal = Calendar.getInstance()
        DatePickerDialog(this, { _, y, m, d ->
            selectedDate = "%04d-%02d-%02d".format(y, m + 1, d)
            binding.dateButton.text = selectedDate
        }, cal.get(Calendar.YEAR), cal.get(Calendar.MONTH), cal.get(Calendar.DAY_OF_MONTH)).show()
    }

    private fun pickTime() {
        val cal = Calendar.getInstance()
        TimePickerDialog(this, { _, h, m ->
            selectedStartTime = "%02d:%02d".format(h, m)
            binding.timeButton.text = "Start: $selectedStartTime"
            // Calculate end time based on selected service duration
            val selectedPos = binding.serviceSpinner.selectedItemPosition
            val duration = if (selectedPos >= 0 && selectedPos < services.size)
                services[selectedPos].duration else 60
            val totalMins = h * 60 + m + duration
            val endH = (totalMins / 60) % 24
            val endM = totalMins % 60
            selectedEndTime = "%02d:%02d".format(endH, endM)
        }, cal.get(Calendar.HOUR_OF_DAY), cal.get(Calendar.MINUTE), true).show()
    }

    private fun confirmBooking(artistId: String) {
        if (selectedDate.isEmpty()) {
            Toast.makeText(this, "Please select a date", Toast.LENGTH_SHORT).show(); return
        }
        if (selectedStartTime.isEmpty()) {
            Toast.makeText(this, "Please select a start time", Toast.LENGTH_SHORT).show(); return
        }
        val selectedPos = binding.serviceSpinner.selectedItemPosition
        if (selectedPos < 0 || selectedPos >= services.size) {
            Toast.makeText(this, "Please select a service", Toast.LENGTH_SHORT).show(); return
        }
        val service = services[selectedPos]
        val notes   = binding.notesInput.text.toString().trim()

        binding.bookButton.isEnabled = false
        binding.progressBar.visibility = View.VISIBLE

        lifecycleScope.launch {
            val result = withContext(Dispatchers.IO) {
                try {
                    ApiClient.get(session.serverUrl).createBooking(
                        session.authHeader,
                        BookingCreateRequest(
                            artist      = artistId,
                            service     = service.id,
                            bookingDate = selectedDate,
                            startTime   = selectedStartTime,
                            endTime     = selectedEndTime,
                            clientNotes = notes
                        )
                    )
                } catch (e: Exception) { null }
            }

            binding.progressBar.visibility = View.GONE
            binding.bookButton.isEnabled   = true

            if (result?.isSuccessful == true) {
                Toast.makeText(
                    this@ArtistDetailActivity,
                    "Booking request sent! The artist will confirm shortly.",
                    Toast.LENGTH_LONG
                ).show()
                finish()
            } else {
                val code = result?.code() ?: 0
                binding.errorText.visibility = View.VISIBLE
                binding.errorText.text = when (code) {
                    400 -> "Invalid booking details. Check date and time."
                    403 -> "Only clients can create bookings."
                    else -> "Booking failed (code $code). Please try again."
                }
            }
        }
    }

    private fun setLoading(on: Boolean) {
        binding.progressBar.visibility = if (on) View.VISIBLE else View.GONE
        binding.contentGroup.visibility = if (on) View.GONE else View.VISIBLE
    }
}
