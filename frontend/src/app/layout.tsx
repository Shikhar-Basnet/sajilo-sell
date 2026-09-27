import ".globals.css";

export const metadata = {
  title: "Sajilo Sell",
  description: "Operating software for Nepal's social sellers",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}