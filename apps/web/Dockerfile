# Multi-stage Dockerfile for Angular SSR (AURA360)
# Optimized build for production deployment on Railway

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (use ci for deterministic builds)
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Build Angular app with SSR
# This creates dist/aura360-front/browser (client) and dist/aura360-front/server (SSR)
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS production

WORKDIR /app

# Copy built artifacts from builder
COPY --from=builder /app/dist/aura360-front ./dist/aura360-front
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package*.json ./

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:4200', (r) => r.statusCode === 200 ? process.exit(0) : process.exit(1))"

# Expose port
EXPOSE 4200

# Set NODE_ENV to production
ENV NODE_ENV=production

# Run SSR server
# Railway will set PORT env var, but we default to 4200
CMD ["sh", "-c", "node dist/aura360-front/server/server.mjs || node dist/aura360-front/server/main.js"]
