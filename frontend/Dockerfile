FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173
RUN chown -R 1000:1000 /app
USER 1000
CMD ["npm", "run", "dev"]
