/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: 'http://127.0.0.1:8000/api/:path*',
            },
            {
                // Serve marketing site at /home
                source: '/home',
                destination: '/home/index.html',
            },
        ];
    },
};

export default nextConfig;
