FROM node:24.22.0-bookworm-slim AS dependencies
WORKDIR /app
COPY package*.json ./
RUN npm ci --include=optional --no-audit --no-fund \
    && ./node_modules/.bin/tsc --version

FROM dependencies AS development
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM dependencies AS build
ARG VITE_FRONTEND_DATA_MODE=django
ENV VITE_FRONTEND_DATA_MODE=$VITE_FRONTEND_DATA_MODE
COPY . .
RUN npm run build

FROM nginx:stable-alpine AS production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/ /usr/share/nginx/html/
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=5s --retries=12 CMD wget -q -O /dev/null http://127.0.0.1/index.html || exit 1
CMD ["nginx", "-g", "daemon off;"]
