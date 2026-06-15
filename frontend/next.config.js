/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  basePath: '/signaldesk',
  trailingSlash: true,
  images: { unoptimized: true },
  reactStrictMode: true,
}

module.exports = nextConfig
