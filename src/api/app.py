"""FastAPI application with Strawberry GraphQL mount and health routes.

This module wires together the GraphQL schema, CORS middleware, and
observability endpoints into a single ASGI application.
"""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from src.api.schema import schema
from src.config.settings import settings
from src.observability.health import router as health_router

app = FastAPI(
    title="EHR-Sync-Pipeline API",
    description="GraphQL API for querying and streaming EHR data",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS middleware (permissive for development)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Health check routes
# ---------------------------------------------------------------------------
app.include_router(health_router)

# ---------------------------------------------------------------------------
# GraphQL (Strawberry) mount with GraphiQL explorer enabled
# ---------------------------------------------------------------------------
graphql_router = GraphQLRouter(schema, graphiql=True)
app.include_router(graphql_router, prefix="/graphql")


def start_api() -> None:
    """Run the API server via uvicorn using centralized settings."""
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)


if __name__ == "__main__":
    start_api()
