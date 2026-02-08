import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: "TokenMeter — Know What You Spend on AI",
  description:
    "LLM API cost tracker and smart router. Track every token, optimize every dollar.",
  openGraph: {
    title: "TokenMeter — Know What You Spend on AI",
    description:
      "Track LLM API costs in real-time. Smart routing saves up to 60% on AI spend.",
    url: "https://tokenmeter.dev",
    siteName: "TokenMeter",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="antialiased">
      <body className="min-h-screen bg-white text-gray-900 flex flex-col">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
