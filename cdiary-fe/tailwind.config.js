/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#8ca9ff',
        secondary: '#aac4f5',
        accent: '#fff2c6',
        background: '#fff8de',
      },
    },
  },
  plugins: [],
}

