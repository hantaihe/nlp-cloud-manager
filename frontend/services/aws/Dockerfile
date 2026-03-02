FROM node:24-alpine AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile

COPY . .

RUN pnpm run build

FROM node:24-alpine

WORKDIR /app
RUN corepack enable && corepack prepare pnpm@latest --activate

RUN pnpm add -g serve

COPY --from=builder /app/dist ./dist

EXPOSE 5174

CMD ["serve", "-s", "dist", "-l", "5174"]
