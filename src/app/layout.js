import { Inter } from "next/font/google";
import Footer from "@/components/layout/Footer";
import Navbar from "@/components/layout/Navbar";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata = {
  title: "FosholCycle | Smarter Crop Rotations",
  description:
    "Explore climate insights, compare crop rotations, and understand seasonal risks across Bangladesh.",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${inter.variable} h-full scroll-pt-20 antialiased`}
    >
      <body className="min-h-full bg-canvas font-sans text-ink">
        <Navbar />
        <main id="main-content" tabIndex={-1}>
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
