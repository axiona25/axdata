/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme colors from mockup
        dark: {
          primary: '#1A1E24',      // Main background
          secondary: '#222B36',    // Sidebar background
          card: '#2B3644',         // Card background
          accent: '#1770EF',       // Primary blue
          'accent-dark': '#0F61DA', // Darker blue
        },
        accent: {
          blue: '#3B82F6',          // Primary accent blue
          orange: '#F59E0B',       // Secondary accent orange
        },
        text: {
          primary: '#FFFFFF',      // Main text
          secondary: '#A0AEC0',    // Secondary text
        },
      },
      fontFamily: {
        sans: ['Inter', 'Arial', 'Helvetica', 'sans-serif'],
      },
      borderRadius: {
        'card': '12px',
        'input': '8px',
        'button': '8px',
      },
    },
  },
  plugins: [],
}
