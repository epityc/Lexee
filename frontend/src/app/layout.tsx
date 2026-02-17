import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lexee — Calculation Engine",
  description: "Moteur de calcul SaaS avec formules protégées",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body className="bg-gray-100 min-h-screen">{children}</body>
    </html>
  );
}
