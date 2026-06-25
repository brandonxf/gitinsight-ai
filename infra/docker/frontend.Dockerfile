FROM node:22-slim

WORKDIR /app

# Instala dependencias primero (cache de capas)
COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

# En desarrollo se sobrescribe con `npm run dev` desde docker-compose.override.yml
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
