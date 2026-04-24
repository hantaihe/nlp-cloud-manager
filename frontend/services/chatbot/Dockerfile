FROM node:24-alpine AS builder

WORKDIR /repo

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY services/aws/package.json services/aws/
COPY services/azure/package.json services/azure/
COPY services/gcp/package.json services/gcp/
COPY services/chatbot/package.json services/chatbot/

RUN pnpm install --frozen-lockfile --filter chatbot...

COPY services/chatbot services/chatbot

RUN pnpm --filter chatbot build

FROM node:24-alpine

WORKDIR /app

COPY --from=builder /repo/package.json /repo/pnpm-workspace.yaml /repo/
COPY --from=builder /repo/node_modules /repo/node_modules
COPY --from=builder /repo/services/chatbot/package.json /repo/services/chatbot/
COPY --from=builder /repo/services/chatbot/node_modules /repo/services/chatbot/node_modules
COPY --from=builder /repo/services/chatbot/build /repo/services/chatbot/build

WORKDIR /repo/services/chatbot

ENV PORT=3106
ENV HOST=0.0.0.0

EXPOSE 3106

CMD ["node", "build"]
