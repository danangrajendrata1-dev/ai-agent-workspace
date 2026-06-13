import "./globals.css";


export const metadata = {
  title: "Personal AI Agent Workspace",
  description: "Private single-user workspace for configuring and monitoring AI agents."
};


export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
