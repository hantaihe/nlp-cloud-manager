# Build context: ../../  (workspace root = frontend/)
FROM node:24-alpine AS builder

WORKDIR /repo

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY services/aws/package.json services/aws/
COPY services/azure/package.json services/azure/
COPY services/gcp/package.json services/gcp/
COPY services/chatbot/package.json services/chatbot/

RUN pnpm install --frozen-lockfile --filter @nlp-cloud-manager/aws...

COPY shared shared
COPY services/aws services/aws

RUN pnpm --filter @nlp-cloud-manager/aws build

FROM node:24-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /repo/services/aws/dist ./dist

EXPOSE 5175

CMD ["serve", "-s", "dist", "-l", "5175"]
