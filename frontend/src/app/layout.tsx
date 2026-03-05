import type { Metadata } from 'next';
import { Inter, Cinzel } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '../components/ThemeProvider';
import { PlanProvider } from '../contexts/PlanContext';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const cinzel = Cinzel({ subsets: ['latin'], variable: '--font-cinzel' });

export const metadata: Metadata = {
  title: 'Quant-Pattern | Astro-Finance App',
  description: 'Precision in Patterns | Data-Driven Trading',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${cinzel.variable} antialiased`} suppressHydrationWarning>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
          <PlanProvider>
            <div className="fixed inset-0 mesh-bg -z-10" />
            {children}
          </PlanProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
