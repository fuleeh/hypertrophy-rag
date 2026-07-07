FROM node:22-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=deps /app/.next/standalone ./
COPY --from=deps /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
