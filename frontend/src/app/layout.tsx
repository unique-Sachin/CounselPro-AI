import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "@/components/providers";
import { AppSidebar } from "@/components/app-sidebar";
import { AppHeader } from "@/components/app-header";
import { GlobalAnalysisOverlay } from "@/components/global-analysis-overlay";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CounselPro AI",
  description: "AI-powered legal counseling platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <Providers>
          <div className="min-h-screen bg-background">
            {/* Desktop sidebar */}
            <aside className="fixed inset-y-0 left-0 z-50 hidden w-64 md:block">
              <AppSidebar />
            </aside>

            {/* Main content */}
            <div className="md:pl-64">
              <AppHeader />
              <main className="flex-1 p-6">
                {children}
              </main>
            </div>

            {/* Global Analysis Overlay */}
            <GlobalAnalysisOverlay />
          </div>
        </Providers>
      </body>
    </html>
  );
}
