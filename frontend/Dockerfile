# frontend/Dockerfile.dev

# Use an official Node runtime as the base image
FROM node:22

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache
COPY package.json package-lock.json ./

# Install dependencies using npm
RUN npm install 

# Copy the rest of the application code
COPY . .

# Set environment variable to allow external access
ENV HOST=0.0.0.0

# Expose the port that CRA runs on
EXPOSE 3000

# Start the development server with hot reloading
CMD ["npm", "start"]

