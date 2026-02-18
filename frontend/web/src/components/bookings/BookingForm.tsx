"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Calendar, Clock, MapPin, Check } from "lucide-react";
import api from "@/lib/api";
import type { ArtistProfile, Service } from "@/types";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";

interface BookingFormProps {
  artist: ArtistProfile;
  onSuccess: () => void;
}

const bookingSchema = z.object({
  scheduled_date: z.string().min(1, "Please select a date"),
  scheduled_time: z.string().min(1, "Please select a time"),
  location: z.string().min(5, "Please enter a valid location"),
  notes: z.string().optional(),
});

type BookingFormData = z.infer<typeof bookingSchema>;

export default function BookingForm({ artist, onSuccess }: BookingFormProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [selectedServices, setSelectedServices] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<BookingFormData>({
    resolver: zodResolver(bookingSchema),
  });

  const createBooking = useMutation({
    mutationFn: async (data: BookingFormData) => {
      const payload = {
        artist_id: artist.id,
        service_ids: selectedServices,
        ...data,
      };
      const { data: booking } = await api.post("/bookings/", payload);
      return booking;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      onSuccess();
      router.push(`/bookings/${data.id}`);
    },
  });

  const toggleService = (serviceId: string) => {
    setSelectedServices((prev) =>
      prev.includes(serviceId)
        ? prev.filter((id) => id !== serviceId)
        : [...prev, serviceId]
    );
  };

  const selectedTotal = artist.services
    .filter((s) => selectedServices.includes(s.id))
    .reduce((sum, s) => sum + s.price, 0);

  const totalDuration = artist.services
    .filter((s) => selectedServices.includes(s.id))
    .reduce((sum, s) => sum + s.duration_minutes, 0);

  // Get tomorrow's date as min
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const minDate = tomorrow.toISOString().split("T")[0];

  return (
    <form
      onSubmit={handleSubmit((data) => createBooking.mutate(data))}
      className="space-y-6"
    >
      {/* Service Selection */}
      <div>
        <h3 className="mb-3 text-sm font-medium text-neutral-700">
          Select Services <span className="text-rose-500">*</span>
        </h3>
        <div className="space-y-2">
          {artist.services
            .filter((s) => s.is_active)
            .map((service) => (
              <button
                key={service.id}
                type="button"
                onClick={() => toggleService(service.id)}
                className={`flex w-full items-center justify-between rounded-xl border-2 p-4 text-left transition-all ${
                  selectedServices.includes(service.id)
                    ? "border-rose-400 bg-rose-50"
                    : "border-neutral-100 hover:border-neutral-200"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 ${
                      selectedServices.includes(service.id)
                        ? "border-rose-500 bg-rose-500"
                        : "border-neutral-300"
                    }`}
                  >
                    {selectedServices.includes(service.id) && (
                      <Check className="h-3 w-3 text-white" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-neutral-900">
                      {service.name}
                    </p>
                    <p className="mt-0.5 text-xs text-neutral-500">
                      {service.description}
                    </p>
                    <p className="mt-1 flex items-center gap-2 text-xs text-neutral-400">
                      <Clock className="h-3 w-3" />
                      {service.duration_minutes} min
                    </p>
                  </div>
                </div>
                <span className="shrink-0 font-semibold text-neutral-900">
                  ${service.price}
                </span>
              </button>
            ))}
        </div>
        {selectedServices.length === 0 && (
          <p className="mt-2 text-xs text-red-500">
            Please select at least one service
          </p>
        )}
      </div>

      {/* Date and Time */}
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Date"
          type="date"
          min={minDate}
          icon={<Calendar className="h-4 w-4" />}
          error={errors.scheduled_date?.message}
          {...register("scheduled_date")}
        />
        <Input
          label="Time"
          type="time"
          icon={<Clock className="h-4 w-4" />}
          error={errors.scheduled_time?.message}
          {...register("scheduled_time")}
        />
      </div>

      {/* Location */}
      <Input
        label="Location"
        placeholder="Enter the appointment address"
        icon={<MapPin className="h-4 w-4" />}
        error={errors.location?.message}
        helperText={`Artist travels up to ${artist.travel_radius_km} km`}
        {...register("location")}
      />

      {/* Notes */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-neutral-700">
          Additional Notes
        </label>
        <textarea
          placeholder="Any special requests, skin type info, reference images, etc."
          rows={3}
          className="w-full rounded-xl border border-neutral-200 bg-white px-4 py-3 text-sm transition-all duration-200 placeholder:text-neutral-400 focus:border-rose-300 focus:outline-none focus:ring-2 focus:ring-rose-100"
          {...register("notes")}
        />
      </div>

      {/* Summary */}
      {selectedServices.length > 0 && (
        <div className="rounded-xl bg-neutral-50 p-4">
          <h4 className="mb-2 text-sm font-medium text-neutral-700">
            Booking Summary
          </h4>
          <div className="space-y-1 text-sm">
            {artist.services
              .filter((s) => selectedServices.includes(s.id))
              .map((s) => (
                <div
                  key={s.id}
                  className="flex justify-between text-neutral-600"
                >
                  <span>{s.name}</span>
                  <span>${s.price}</span>
                </div>
              ))}
            <div className="mt-2 border-t border-neutral-200 pt-2">
              <div className="flex justify-between text-neutral-500">
                <span>Estimated Duration</span>
                <span>{totalDuration} min</span>
              </div>
              <div className="flex justify-between font-semibold text-neutral-900">
                <span>Total</span>
                <span>${selectedTotal}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error display */}
      {createBooking.isError && (
        <div className="rounded-xl bg-red-50 p-4 text-sm text-red-600">
          Failed to create booking. Please try again.
        </div>
      )}

      {/* Submit */}
      <Button
        type="submit"
        variant="primary"
        size="lg"
        className="w-full"
        isLoading={createBooking.isPending}
        disabled={selectedServices.length === 0}
      >
        Confirm Booking - ${selectedTotal}
      </Button>
    </form>
  );
}
