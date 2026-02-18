import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        rose: {
          50: "#fff1f2",
          100: "#ffe4e6",
          200: "#fecdd3",
          300: "#fda4af",
          400: "#fb7185",
          500: "#f43f5e",
          600: "#e11d48",
          700: "#be123c",
          800: "#9f1239",
          900: "#881337",
          950: "#4c0519",
        },
        blush: {
          50: "#fdf2f8",
          100: "#fce7f3",
          200: "#fbcfe8",
          300: "#f9a8d4",
          400: "#f472b6",
          500: "#ec4899",
          600: "#db2777",
          700: "#be185d",
          800: "#9d174d",
          900: "#831843",
          950: "#500724",
        },
        glam: {
          50: "#fefce8",
          100: "#fef9c3",
          200: "#fef08a",
          300: "#fde047",
          400: "#facc15",
          500: "#d4a017",
          600: "#b8860b",
          700: "#92710c",
          800: "#7a6012",
          900: "#674f15",
          950: "#3d2e08",
        },
        neutral: {
          50: "#fafafa",
          100: "#f5f5f5",
          200: "#e5e5e5",
          300: "#d4d4d4",
          400: "#a3a3a3",
          500: "#737373",
          600: "#525252",
          700: "#404040",
          800: "#262626",
          900: "#171717",
          950: "#0a0a0a",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Playfair Display", "serif"],
      },
      backgroundImage: {
        "gradient-glam":
          "linear-gradient(135deg, #fdf2f8 0%, #fff1f2 50%, #fefce8 100%)",
        "gradient-rose":
          "linear-gradient(135deg, #e11d48 0%, #ec4899 50%, #f472b6 100%)",
        "gradient-dark":
          "linear-gradient(135deg, #171717 0%, #262626 50%, #404040 100%)",
      },
      boxShadow: {
        glam: "0 4px 20px -2px rgba(244, 63, 94, 0.15)",
        "glam-lg": "0 10px 40px -4px rgba(244, 63, 94, 0.2)",
      },
    },
  },
  plugins: [],
};

export default config;
