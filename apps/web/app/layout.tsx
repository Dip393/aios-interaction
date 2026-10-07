import './globals.css';

import type {
  Metadata,
  Viewport,
} from 'next';

export const metadata: Metadata = {
  title: {
    default: 'AIOS Runtime',
    template: '%s | AIOS Runtime',
  },

  description:
    'Intent-driven AI operating environment for planning, execution, memory, environments, voice, vision and intelligent automation.',

  applicationName:
    'AIOS Runtime',

  keywords: [
    'AIOS',
    'AI Operating System',
    'Artificial Intelligence',
    'AI Runtime',
    'Intent-driven computing',
    'AI agents',
    'AI automation',
  ],

  robots: {
    index: false,
    follow: false,
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}