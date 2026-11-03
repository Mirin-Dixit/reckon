import type { Metadata } from "next";
import type { ReactNode } from "react";
import localFont from "next/font/local";
import "./globals.css";

const serif = localFont({ src: [
  { path: "./fonts/serif-latin.woff2", weight: "200 900", style: "normal" },
  { path: "./fonts/serif-italic-latin.woff2", weight: "200 900", style: "italic" },
], variable: "--font-source-serif", display: "swap", fallback: ["Georgia"], adjustFontFallback: "Times New Roman", preload: true });
const sans = localFont({ src: "./fonts/sans-latin.woff2", weight: "100 700", variable: "--font-plex-sans", display: "swap", fallback: ["Arial"], preload: true });
const mono = localFont({ src: "./fonts/mono-latin.woff2", weight: "400", variable: "--font-plex-mono", display: "swap", fallback: ["Courier New"], preload: true });

export const metadata: Metadata = {
  title: "Workbench | RAGBench Studio",
  description: "Local research workbench for inspecting RAG system readiness.",
  icons: { icon: "/icon.svg" },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="en" className={`${serif.variable} ${sans.variable} ${mono.variable}`}><body>{children}</body></html>;
}
