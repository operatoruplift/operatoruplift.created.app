# Operator Uplift API Documentation

## Overview

The Operator Uplift platform provides a comprehensive API for interacting with AI agents powered by Gemini 3 Pro.

## Authentication

All API requests require authentication using an API key:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.operatoruplift.created.app/v1/agents
```

## Endpoints

### Agents

#### List Agents

```
GET /api/v1/agents
```

Returns a list of available AI agents.

#### Create Agent

```
POST /api/v1/agents
```

Create a new AI agent with custom configuration.

#### Get Agent Details

```
GET /api/v1/agents/:id
```

Retrieve details for a specific agent.

### Tasks

#### Execute Task

```
POST /api/v1/tasks
```

Execute a task using an AI agent.

**Request Body:**

```json
{
  "agentId": "agent-123",
  "task": "Analyze this document",
  "parameters": {
    "model": "gemini-3-pro",
    "temperature": 0.7
  }
}
```

**Response:**

```json
{
  "taskId": "task-456",
  "status": "processing",
  "result": null
}
```

## Rate Limits

- 100 requests per minute for free tier
- 1000 requests per minute for pro tier

## Error Codes

- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## SDK Support

Official SDKs available for:
- JavaScript/TypeScript
- Python
- Go

## Support

For API support, contact: api-support@operatoruplift.created.app
