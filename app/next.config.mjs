const nextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**' },
    ],
  },
  serverRuntimeConfig: {
    apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000',
  },
  eslint: { ignoreDuringBuilds: true },
  reactStrictMode: true,
  typescript: { ignoreBuildErrors: true },
  poweredByHeader: false
};

export default nextConfig;
