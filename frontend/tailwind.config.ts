import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        lexee: {
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
        },
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "tooltip-in": "tooltipIn 0.15s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(-4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        tooltipIn: {
          "0%": { opacity: "0", transform: "translateX(-4px) translateY(-50%)" },
          "100%": { opacity: "1", transform: "translateX(0) translateY(-50%)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
