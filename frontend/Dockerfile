# syntax = docker/dockerfile:1.2
FROM node:14-alpine
EXPOSE 3000

# Set up base platform
RUN apk --no-cache add --update python3 make g++ curl

# Prepare node modules
RUN mkdir -p /home/node
COPY ./app /home/node/app
WORKDIR /home/node/app/sip2-ckan/
RUN --mount=type=cache,target=/root/.npm npm install

# Server configuration on build
ARG SERVER_HOST
ARG BACKEND_API
ARG API_LOG
RUN echo "SERVER_HOST: $SERVER_HOST"
RUN echo "BACKEND_API: $BACKEND_API"
RUN echo "API_LOG: $API_LOG"

# Build and start
RUN ["npm", "run", "build"]
CMD npm start
