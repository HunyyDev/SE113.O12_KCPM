---
title: Traffic Detection
emoji: 🐾
colorFrom: yellow
colorTo: pink
sdk: docker
pinned: false
app_port: 3000
---

## Prerequisite:
Before you proceed, make sure you have installed/created the following application/service:
1. Docker, link at: https://www.docker.com
2. Supabase, you can self-host the service or create a free Supabase project at: https://supabase.com
3. Firebase, you can create a free Firebase project at: https://firebase.google.com
4. Neo4j database, you can create free at: https://neo4j.com

## Configuration
Open up `compose.yaml`, change all the environment variable:
```
environment:
  - SUPABASE_URL=your-supabase-url
  - SUPABASE_KEY=your-supabase-key
  - FIREBASE_CREDENTIALS=your-firebase-credentials
  - FIREBASE_API_KEY=your-firebase-api-key
  - NEO4J_URI=your-neo4j-uri
  - NEO4J_USERNAME=your-neo4j-username
  - NEO4J_PASSWORD=your-neo4j-password
```

```
docker compose up -d
```
