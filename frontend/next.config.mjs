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
  basePath: process.env.GITHUB_PAGES ? '/aive' : '',
  assetPrefix: process.env.GITHUB_PAGES ? '/aive' : '',
}

export default nextConfig
