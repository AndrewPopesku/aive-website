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
  basePath: process.env.NODE_ENV === 'production' ? '/aive-website' : '',
  assetPrefix: process.env.NODE_ENV === 'production' ? '/aive-website/' : '',
}

export default nextConfig
