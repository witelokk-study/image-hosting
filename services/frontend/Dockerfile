FROM nginx:1.27-alpine

# Copy static assets
COPY static /usr/share/nginx/html
COPY default.conf /etc/nginx/conf.d/default.conf

# Generate runtime config for API base URL
COPY docker-entrypoint.sh /docker-entrypoint.d/99-app-config.sh
RUN chmod +x /docker-entrypoint.d/99-app-config.sh

EXPOSE 80
