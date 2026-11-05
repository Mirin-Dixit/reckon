FROM node:24-bookworm-slim@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c AS build
WORKDIR /work/frontend
ENV NEXT_TELEMETRY_DISABLED=1 RECKON_STANDALONE=1
ARG NEXT_PUBLIC_RECKON_API_BASE_URL=http://127.0.0.1:3000
ENV NEXT_PUBLIC_RECKON_API_BASE_URL=$NEXT_PUBLIC_RECKON_API_BASE_URL
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM node:24-bookworm-slim@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=127.0.0.1 PORT=3000
COPY --from=build --chown=node:node /work/frontend/.next/standalone ./
COPY --from=build --chown=node:node /work/frontend/.next/static ./.next/static
COPY --from=build --chown=node:node /work/frontend/public ./public
USER node
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
    CMD node -e "fetch('http://127.0.0.1:3000/evaluation').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["node", "server.js"]
