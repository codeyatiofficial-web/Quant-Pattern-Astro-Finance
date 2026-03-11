import type { Metadata } from 'next';
import { Inter, Cinzel } from 'next/font/google';
import Script from 'next/script';
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
      <Script
        id="fb-pixel"
        strategy="afterInteractive"
        dangerouslySetInnerHTML={{
          __html: `
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '637604245384711');
fbq('track', 'PageView');
            `,
        }}
      />
      <body className={`${inter.variable} ${cinzel.variable} antialiased`} suppressHydrationWarning>
        <noscript>
          <img
            height="1"
            width="1"
            style={{ display: 'none' }}
            src="https://www.facebook.com/tr?id=637604245384711&ev=PageView&noscript=1"
            alt=""
          />
        </noscript>
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
