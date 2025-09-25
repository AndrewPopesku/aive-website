/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  output: 'export',
  distDir: 'out',
  trailingSlash: true,
  // Only use basePath/assetPrefix for GitHub Pages build
  ...(process.env.GITHUB_PAGES && {
    basePath: '/aive',
    assetPrefix: '/aive',
  }),
}

export default nextConfig
