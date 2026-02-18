"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Mail,
  Lock,
  User,
  Phone,
  Sparkles,
  Eye,
  EyeOff,
  Palette,
  Heart,
} from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import type { UserRole } from "@/types";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";

const registerSchema = z
  .object({
    first_name: z.string().min(2, "First name must be at least 2 characters"),
    last_name: z.string().min(2, "Last name must be at least 2 characters"),
    email: z.string().email("Please enter a valid email address"),
    phone: z.string().optional(),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[0-9]/, "Password must contain at least one number"),
    confirm_password: z.string(),
    role: z.enum(["client", "artist"]),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser, isLoading, error, clearError } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [selectedRole, setSelectedRole] = useState<UserRole>("client");

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      role: "client",
    },
  });

  const onSubmit = async (data: RegisterForm) => {
    try {
      const { confirm_password, ...registerData } = data;
      void confirm_password;
      await registerUser(registerData);
      router.push(data.role === "artist" ? "/dashboard" : "/artists");
    } catch {
      // Error handled by store
    }
  };

  const handleRoleSelect = (role: UserRole) => {
    setSelectedRole(role);
    setValue("role", role);
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-gradient-glam px-4 py-12">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-500 to-blush-500 shadow-glam">
            <Sparkles className="h-7 w-7 text-white" />
          </div>
          <h1 className="font-display text-3xl font-bold text-neutral-900">
            Join GlamConnect
          </h1>
          <p className="mt-2 text-neutral-500">
            Create your account and start your beauty journey
          </p>
        </div>

        {/* Form */}
        <div className="rounded-2xl border border-neutral-100 bg-white p-8 shadow-sm">
          {error && (
            <div className="mb-6 rounded-xl bg-red-50 p-4 text-sm text-red-600">
              {error}
              <button
                onClick={clearError}
                className="ml-2 font-medium underline"
              >
                Dismiss
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Role Selection */}
            <div>
              <label className="mb-2 block text-sm font-medium text-neutral-700">
                I want to join as
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => handleRoleSelect("client")}
                  className={`flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition-all ${
                    selectedRole === "client"
                      ? "border-rose-400 bg-rose-50 text-rose-700"
                      : "border-neutral-200 text-neutral-500 hover:border-neutral-300"
                  }`}
                >
                  <Heart
                    className={`h-6 w-6 ${
                      selectedRole === "client"
                        ? "text-rose-500"
                        : "text-neutral-400"
                    }`}
                  />
                  <span className="text-sm font-semibold">Client</span>
                  <span className="text-xs opacity-70">
                    I want to book artists
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => handleRoleSelect("artist")}
                  className={`flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition-all ${
                    selectedRole === "artist"
                      ? "border-rose-400 bg-rose-50 text-rose-700"
                      : "border-neutral-200 text-neutral-500 hover:border-neutral-300"
                  }`}
                >
                  <Palette
                    className={`h-6 w-6 ${
                      selectedRole === "artist"
                        ? "text-rose-500"
                        : "text-neutral-400"
                    }`}
                  />
                  <span className="text-sm font-semibold">Artist</span>
                  <span className="text-xs opacity-70">
                    I offer makeup services
                  </span>
                </button>
              </div>
              <input type="hidden" {...register("role")} />
            </div>

            {/* Name fields */}
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="First Name"
                placeholder="Jane"
                icon={<User className="h-4 w-4" />}
                error={errors.first_name?.message}
                {...register("first_name")}
              />
              <Input
                label="Last Name"
                placeholder="Doe"
                error={errors.last_name?.message}
                {...register("last_name")}
              />
            </div>

            <Input
              label="Email Address"
              type="email"
              placeholder="you@example.com"
              icon={<Mail className="h-4 w-4" />}
              error={errors.email?.message}
              {...register("email")}
            />

            <Input
              label="Phone Number"
              type="tel"
              placeholder="+1 (555) 000-0000"
              icon={<Phone className="h-4 w-4" />}
              helperText="Optional, but helps with booking confirmations"
              {...register("phone")}
            />

            <div className="relative">
              <Input
                label="Password"
                type={showPassword ? "text" : "password"}
                placeholder="Create a strong password"
                icon={<Lock className="h-4 w-4" />}
                error={errors.password?.message}
                {...register("password")}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-[38px] text-neutral-400 hover:text-neutral-600"
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>

            <Input
              label="Confirm Password"
              type="password"
              placeholder="Re-enter your password"
              icon={<Lock className="h-4 w-4" />}
              error={errors.confirm_password?.message}
              {...register("confirm_password")}
            />

            <div className="flex items-start gap-2">
              <input
                type="checkbox"
                required
                className="mt-1 rounded border-neutral-300 text-rose-500 focus:ring-rose-200"
              />
              <label className="text-xs text-neutral-500">
                I agree to the{" "}
                <Link
                  href="/terms"
                  className="font-medium text-rose-600 hover:text-rose-700"
                >
                  Terms of Service
                </Link>{" "}
                and{" "}
                <Link
                  href="/privacy"
                  className="font-medium text-rose-600 hover:text-rose-700"
                >
                  Privacy Policy
                </Link>
              </label>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isLoading}
              className="w-full"
            >
              Create Account
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-neutral-500">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-semibold text-rose-600 hover:text-rose-700"
            >
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
