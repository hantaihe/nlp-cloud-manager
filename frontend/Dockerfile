FROM node:24-alpine AS builder

WORKDIR /repo

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY services/aws/package.json services/aws/
COPY services/azure/package.json services/azure/
COPY services/gcp/package.json services/gcp/
COPY services/chatbot/package.json services/chatbot/

RUN pnpm install --frozen-lockfile --filter base...

COPY . .

RUN pnpm --filter base build

FROM node:24-alpine

WORKDIR /app

COPY --from=builder /repo/build ./build
COPY --from=builder /repo/node_modules ./node_modules
COPY --from=builder /repo/package.json ./

ENV PORT=3000
ENV HOST=0.0.0.0

EXPOSE 3000

CMD ["node", "build"]
