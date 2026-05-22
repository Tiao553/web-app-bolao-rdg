const nextConfig = {
  distDir: '.next-local',
  eslint: {
    ignoreDuringBuilds: true
  },
  reactStrictMode: true,
  typescript: {
    ignoreBuildErrors: true
  },
  poweredByHeader: false
};

export default nextConfig;
