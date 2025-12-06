import { DM_Sans } from "next/font/google";
import type { Metadata } from "next";
import "./globals.css";
import { BlockNavigationProvider } from "./providers/BlockNavigationProvider";

export const metadata: Metadata = {
  title: "Blundr",
};

const font = DM_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-dm-sans",
  weight: ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${font.variable}`}
    >
      <body className="relative min-h-screen antialiased">
        <BlockNavigationProvider>{children}</BlockNavigationProvider>
      </body>
    </html>
  );
}
