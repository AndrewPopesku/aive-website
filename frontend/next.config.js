/** @type {import('next').NextConfig} */
const nextConfig = {
  // Reduce file watching sensitivity
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        poll: 1000, // Check for changes every second instead of constantly
        aggregateTimeout: 300, // Delay before rebuilding
        ignored: [
          '**/node_modules/**',
          '**/.git/**',
          '**/.next/**',
          '**/dist/**',
          '**/build/**',
          '**/.DS_Store',
          '**/Thumbs.db',
        ],
      };
    }
    return config;
  },
  
  // Experimental features that can help with performance
  experimental: {
    turbo: {
      // Use Turbopack for faster builds (Next.js 13+)
    },
  },
};

module.exports = nextConfig;