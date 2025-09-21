FROM node:20-slim

WORKDIR /app

# Copy package.json files
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the frontend code
COPY frontend/ .

# Build the Next.js application
RUN npm run build

# Run the application
CMD ["npm", "start"] 