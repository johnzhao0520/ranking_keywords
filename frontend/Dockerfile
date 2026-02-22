FROM node:20-alpine AS builder

WORKDIR /app

# Copy and build frontend
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Final stage
FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /app
COPY --from=builder /app/out ./out

# Use static file server
EXPOSE 3000
CMD ["sh", "-c", "echo 'Static site ready' && tail -f /dev/null"]
