/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fdf8f0",
          100: "#f8ecd8",
          500: "#c2812f",
          600: "#a4691f",
          700: "#82531b",
          900: "#4a2f10",
        },
      },
    },
  },
  plugins: [],
};
