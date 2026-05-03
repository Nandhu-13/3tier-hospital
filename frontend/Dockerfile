FROM nginx:1.25-alpine

COPY src/index.html /usr/share/nginx/html/index.html
COPY nginx.conf     /etc/nginx/conf.d/default.conf

RUN chown -R nginx:nginx /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
