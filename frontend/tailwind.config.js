/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      borderRadius: {
        lg:  "14px",
        md:  "10px",
        sm:  "8px",
        xl:  "16px",
        "2xl": "20px",
      },
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input:  "hsl(var(--input))",
        ring:   "hsl(var(--ring))",
        chart: {
          "1": "hsl(var(--chart-1))",
          "2": "hsl(var(--chart-2))",
          "3": "hsl(var(--chart-3))",
          "4": "hsl(var(--chart-4))",
          "5": "hsl(var(--chart-5))",
        },
        /* Palette FABS-CI V10 — dark SaaS */
        fabs: {
          bg:        "#0B1220",
          sidebar:   "#111827",
          card:      "#1E293B",
          text:      "#E2E8F0",
          muted:     "#94A3B8",
          border:    "rgba(255,255,255,0.08)",
          primary:   "#F97316",
          "primary-dark": "#EA6C0A",
          dashboard: "#3B82F6",
          commerce:  "#F97316",
          stock:     "#10B981",
          finance:   "#14B8A6",
          rh:        "#8B5CF6",
          notif:     "#EF4444",
          docs:      "#F59E0B",
          admin:     "#6366F1",
          success:   "#10B981",
          warning:   "#F59E0B",
          error:     "#EF4444",
        },
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to:   { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to:   { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up":   "accordion-up 0.2s ease-out",
      },
      boxShadow: {
        "fabs-sm":  "0 2px 8px rgba(0,0,0,0.25)",
        "fabs-md":  "0 4px 24px rgba(0,0,0,0.3)",
        "fabs-lg":  "0 8px 40px rgba(0,0,0,0.4)",
        "fabs-xl":  "0 20px 60px rgba(0,0,0,0.5)",
        "orange":   "0 4px 14px rgba(249,115,22,0.35)",
        "orange-lg":"0 8px 28px rgba(249,115,22,0.45)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
