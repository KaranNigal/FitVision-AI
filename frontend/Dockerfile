FROM node:18-alpine

WORKDIR /app

# Copy dependency catalogs
COPY package.json ./

# Install npm modules
RUN npm install

# Copy source directories
COPY . .

# Expose Vite Port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev"]
