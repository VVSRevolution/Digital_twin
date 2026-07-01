# front/Dockerfile

# 🔥 Estágio 1: Build com Node.js 22
FROM node:22-alpine AS builder

WORKDIR /app

# Copia e instala dependências
COPY package*.json ./
RUN npm ci --silent

# Copia o código e constrói
COPY . .
RUN npm run build --silent

# 🔥 Estágio 2: Produção com Node.js 22
FROM node:22-alpine

WORKDIR /app

# Copia o build do Nuxt
COPY --from=builder /app/.output ./.output

EXPOSE 3000

# Comando para rodar NUXT em produção
CMD ["node", ".output/server/index.mjs"]