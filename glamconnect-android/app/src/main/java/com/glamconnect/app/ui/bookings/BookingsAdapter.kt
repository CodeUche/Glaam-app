package com.glamconnect.app.ui.bookings

import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.glamconnect.app.R
import com.glamconnect.app.data.Booking
import com.glamconnect.app.databinding.ItemBookingBinding

class BookingsAdapter(
    private val bookings: List<Booking>,
    private val isClientView: Boolean = false,
    private val onCancel: ((Booking) -> Unit)? = null
) : RecyclerView.Adapter<BookingsAdapter.VH>() {

    inner class VH(val binding: ItemBookingBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val b = ItemBookingBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return VH(b)
    }

    override fun getItemCount() = bookings.size

    override fun onBindViewHolder(holder: VH, position: Int) {
        val booking = bookings[position]
        val b = holder.binding

        // Show artist name for clients, client name for artists/admins
        b.primaryNameText.text = if (isClientView) {
            booking.artistName ?: booking.service?.let { "Artist" } ?: "Unknown artist"
        } else {
            booking.client?.fullName() ?: "Unknown client"
        }

        b.serviceText.text = booking.service?.name ?: "Unknown service"
        b.priceText.text   = booking.service?.let { "$${it.price}" } ?: "—"
        b.dateText.text    = booking.bookingDate?.take(10) ?: "—"

        val (label, bg, fg) = when (booking.status) {
            "pending"   -> Triple("Pending",   "#FEF3C7", "#D97706")
            "confirmed" -> Triple("Confirmed", "#D1FAE5", "#059669")
            "completed" -> Triple("Completed", "#DBEAFE", "#1D4ED8")
            "cancelled" -> Triple("Cancelled", "#FEE2E2", "#DC2626")
            else        -> Triple(booking.status.replaceFirstChar { it.uppercase() }, "#F5F5F5", "#424242")
        }

        b.statusBadge.text = label
        b.statusBadge.setTextColor(Color.parseColor(fg))
        b.statusBadge.setBackgroundColor(Color.parseColor(bg))

        // Cancel button: visible for clients with pending bookings
        if (isClientView && booking.status == "pending" && onCancel != null) {
            b.cancelButton.visibility = View.VISIBLE
            b.cancelButton.setOnClickListener { onCancel.invoke(booking) }
        } else {
            b.cancelButton.visibility = View.GONE
        }
    }
}
