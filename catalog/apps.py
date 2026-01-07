from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """
    Catalog application configuration.

    The catalog app exposes public, read-only APIs that power the
    institution’s archival catalog interface.

    Responsibilities:
        - Serve denormalized, read-optimized data for public consumption
        - Support browsing, searching, and discovery use cases
        - Aggregate data from internal domain apps (archival units,
          finding aids, containers, authority records, etc.)

    Design principles:
        - Read-only endpoints
        - Stable response schemas for frontend usage
        - No internal workflow or administrative logic
        - Safe for unauthenticated and external access
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'
