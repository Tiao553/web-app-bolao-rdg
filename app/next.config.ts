import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'standalone',

  // Allow images from any https source (flags, team logos)
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**' },
    ],
  },

  // Expose backend URL to server-side code only (not bundled into client JS)
  serverRuntimeConfig: {
    apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000',
  },
};

export default nextConfig;
