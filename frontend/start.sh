#!/bin/sh

# Generate runtime configuration based on environment variables
cat > /usr/share/nginx/html/config.js << EOF
// Runtime configuration for the frontend
// This file is dynamically generated at container startup
window.APP_CONFIG = {
  API_BASE_URL: '${VITE_API_BASE_URL:-/api}'
};
EOF

# Start nginx
exec nginx -g "daemon off;"