const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**' },
    ],
  },
  eslint: { ignoreDuringBuilds: true },
  reactStrictMode: true,
  typescript: { ignoreBuildErrors: true },
  poweredByHeader: false
};

export default nextConfig;
