import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI & Data News Wiki",
  description: "AI·데이터 뉴스 지식 베이스",
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
