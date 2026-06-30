# Estágio 1: Build
FROM node:18-alpine AS builder

WORKDIR /app

# Copia e instala dependências
COPY package*.json ./
RUN npm ci --silent

# Copia o código e constrói
COPY . .
RUN npm run build --silent

# Estágio 2: Servidor de produção
FROM node:18-alpine

WORKDIR /app

# Copia o build
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./

# Instala o servidor vite
RUN npm install -g vite

EXPOSE 3000

# Serve o build
CMD ["vite", "preview", "--host", "0.0.0.0", "--port", "3000"]