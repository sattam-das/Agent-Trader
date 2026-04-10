/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080C16",
        foreground: "#FFFFFF",
        card: {
          DEFAULT: "#0D1322",
          foreground: "#FFFFFF",
        },
        popover: {
          DEFAULT: "#0D1322",
          foreground: "#FFFFFF",
        },
        primary: {
          DEFAULT: "#0066FF",
          foreground: "#FFFFFF",
        },
        secondary: {
          DEFAULT: "#1a243d",
          foreground: "#8B95A5",
        },
        muted: {
          DEFAULT: "#1a243d",
          foreground: "#8B95A5",
        },
        accent: {
          DEFAULT: "#1a243d",
          foreground: "#FFFFFF",
        },
        destructive: {
          DEFAULT: "#FF3B30",
          foreground: "#FFFFFF",
        },
        success: {
          DEFAULT: "#34C759",
          foreground: "#FFFFFF",
        },
        border: "#1a243d",
        input: "#1a243d",
        ring: "#0066FF",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
