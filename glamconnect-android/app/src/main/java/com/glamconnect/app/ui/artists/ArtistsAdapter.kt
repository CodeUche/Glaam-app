package com.glamconnect.app.ui.artists

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.glamconnect.app.data.ArtistProfile
import com.glamconnect.app.databinding.ItemArtistBinding

class ArtistsAdapter(
    private val artists: List<ArtistProfile>,
    private val onBookClick: ((ArtistProfile) -> Unit)? = null
) : RecyclerView.Adapter<ArtistsAdapter.VH>() {

    inner class VH(val binding: ItemArtistBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val b = ItemArtistBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return VH(b)
    }

    override fun getItemCount() = artists.size

    override fun onBindViewHolder(holder: VH, position: Int) {
        val artist = artists[position]
        val b = holder.binding

        b.nameText.text     = artist.user.fullName()
        b.locationText.text = artist.location?.ifEmpty { "Location not set" } ?: "Location not set"
        b.rateText.text     = "$${artist.hourlyRate}/hr"

        if (!artist.bio.isNullOrEmpty()) {
            b.bioText.text       = artist.bio.take(120) + if (artist.bio.length > 120) "..." else ""
            b.bioText.visibility = View.VISIBLE
        } else {
            b.bioText.visibility = View.GONE
        }

        val specialties = artist.specialties?.take(4)
        if (!specialties.isNullOrEmpty()) {
            b.specialtiesText.text       = specialties.joinToString(" - ")
            b.specialtiesText.visibility = View.VISIBLE
        } else {
            b.specialtiesText.visibility = View.GONE
        }

        if (artist.isAvailable) {
            b.availabilityBadge.text = "Available"
            b.availabilityBadge.setTextColor(android.graphics.Color.parseColor("#059669"))
            b.availabilityBadge.setBackgroundColor(android.graphics.Color.parseColor("#D1FAE5"))
        } else {
            b.availabilityBadge.text = "Unavailable"
            b.availabilityBadge.setTextColor(android.graphics.Color.parseColor("#DC2626"))
            b.availabilityBadge.setBackgroundColor(android.graphics.Color.parseColor("#FEE2E2"))
        }

        val rating = artist.averageRating
        if (rating != null && rating > 0.0) {
            b.ratingText.text       = "* ${"%.1f".format(rating)} (${artist.totalReviews ?: 0})"
            b.ratingText.visibility = View.VISIBLE
        } else {
            b.ratingText.visibility = View.GONE
        }

        // Show Book Now button only when click handler is provided (clients)
        if (onBookClick != null) {
            b.bookButton.visibility = View.VISIBLE
            b.bookButton.setOnClickListener { onBookClick.invoke(artist) }
        } else {
            b.bookButton.visibility = View.GONE
        }
    }
}
