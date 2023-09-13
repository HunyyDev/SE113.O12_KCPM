FROM node:18

WORKDIR /app

COPY package*.json .

RUN npm ci --omit=dev

COPY . .

EXPOSE 3000 5555

ENV NODE_ENV=production

CMD ["node", "server.js"]
