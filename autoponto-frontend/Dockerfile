FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_API_URL=/api
ARG VITE_BASE_PATH=/
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BASE_PATH=$VITE_BASE_PATH

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

ARG NGINX_CONF=nginx.conf
ARG VITE_BASE_PATH=/

COPY ${NGINX_CONF} /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /tmp/autoponto-dist
RUN cp -r /tmp/autoponto-dist/. /usr/share/nginx/html/ \
    && if [ "$VITE_BASE_PATH" != "/" ]; then \
      prefix="$(echo "$VITE_BASE_PATH" | sed 's#^/##; s#/$##')" \
      && mkdir -p "/usr/share/nginx/html/$prefix" \
      && cp -r /tmp/autoponto-dist/. "/usr/share/nginx/html/$prefix/"; \
    fi \
    && rm -rf /tmp/autoponto-dist

EXPOSE 80
