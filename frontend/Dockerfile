# Multi-stage build for React-Vite app
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Accept build argument for docker-compose
ARG DOCKER_COMPOSE=false
ENV DOCKER_COMPOSE=$DOCKER_COMPOSE

# Build the application
RUN npm run build

# Production image, copy all the files and run nginx
FROM nginx:1.25-alpine AS runner
WORKDIR /app

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Create a simple health check endpoint
RUN echo '<!DOCTYPE html><html><head><title>Health Check</title></head><body><h1>OK</h1></body></html>' > /usr/share/nginx/html/health

# Expose port 80
EXPOSE 80

# Start nginx with dynamic configuration
CMD ["/start.sh"]