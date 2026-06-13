/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx}",
    "./components/**/*.{js,jsx}",
    "./lib/**/*.{js,jsx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: "#10243b",
        mist: "#edf3f7",
        line: "#d6e0e8",
        accent: "#1c6b5c",
        sand: "#f7f3ea"
      },
      boxShadow: {
        panel: "0 18px 45px rgba(16, 36, 59, 0.08)"
      }
    }
  },
  plugins: []
};
