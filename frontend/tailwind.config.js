/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'space': '#050810',
        'card': '#111827',
        'isro': '#FF6B35',
        'isro-dim': '#FF6B3540',
        'electric': '#00D4FF',
      },
      fontFamily: {
        'space': ['Space Grotesk', 'sans-serif'],
        'inter': ['Inter', 'sans-serif'],
        'mono': ['JetBrains Mono', 'monospace'],
      },
      backdropBlur: {
        'glass': '12px',
      },
    },
  },
  plugins: [],
}