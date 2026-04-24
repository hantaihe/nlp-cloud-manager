FROM node:24-alpine AS builder

WORKDIR /repo

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY services/aws/package.json services/aws/
COPY services/azure/package.json services/azure/
COPY services/gcp/package.json services/gcp/
COPY services/chatbot/package.json services/chatbot/

RUN pnpm install --frozen-lockfile --filter gcp...

COPY shared shared
COPY services/gcp services/gcp

RUN pnpm --filter gcp build

FROM node:24-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /repo/services/gcp/dist ./dist

EXPOSE 5177

CMD ["serve", "-s", "dist", "-l", "5177"]
