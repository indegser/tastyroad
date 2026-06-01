import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "맛집 최신 크롤링",
  description: "유튜브 RSS에서 수집한 맛집 후보를 최신순으로 보여줍니다.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
