/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    screens: {
      xs: '375px',
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
      '2xl': '1536px',
    },
    extend: {
      boxShadow: {
        glow: '0 0 0 1px rgba(45, 212, 191, .22), 0 18px 50px rgba(2, 6, 23, .42)',
      },
    },
  },
  plugins: [],
};
