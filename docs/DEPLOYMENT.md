# Deployment Guide

## Operator Uplift Deployment Options

### Option 1: Vercel (Recommended)

1. Connect your GitHub repository to Vercel
2. Configure environment variables
3. Deploy automatically on push

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Option 2: Self-Hosted

#### Requirements
- Node.js v18+
- 2GB RAM minimum
- SSL certificate for HTTPS

#### Steps

```bash
# Build the application
npm run build

# Start production server
npm start
```

#### Using PM2

```bash
# Install PM2
npm install -g pm2

# Start application
pm2 start npm --name "operatoruplift" -- start

# Configure PM2 to start on system boot
pm2 startup
pm2 save
```

### Option 3: Docker

Create a `Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

Build and run:

```bash
docker build -t operatoruplift .
docker run -p 3000:3000 -e GEMINI_API_KEY=your_key operatoruplift
```

### Environment Variables

Ensure these are set in production:

- `GEMINI_API_KEY`
- `NODE_ENV=production`
- `NEXT_PUBLIC_APP_URL`

### SSL/HTTPS

For production, always use HTTPS. Options:
- Cloudflare
- Let's Encrypt
- Cloud provider SSL

### Monitoring

Recommended monitoring tools:
- Vercel Analytics
- Sentry for error tracking
- Google Analytics

### Backup Strategy

1. Database backups (if applicable)
2. Environment variables backup
3. Regular code commits

## Scaling

For high-traffic scenarios:
- Use CDN for static assets
- Implement caching strategies
- Consider serverless functions
- Load balancing for multiple instances
