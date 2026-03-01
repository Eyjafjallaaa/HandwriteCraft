import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "迹墨 HandwriteCraft - 智能手写生成",
  description: "将文本转换为逼真的手写体图片，支持 PDF/图片背景",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
          {children}
        </div>
      </body>
    </html>
  );
}
