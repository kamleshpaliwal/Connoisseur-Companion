"""MCP server exposing the deterministic restaurant services."""

from mcp.server.fastmcp import FastMCP

from connoisseur_companion.services import RestaurantService


service = RestaurantService()
mcp = FastMCP("Connoisseur Companion", json_response=True)


@mcp.tool()
def get_restaurant_info(item_id: int) -> dict | None:
    """Get details for a restaurant by its item ID."""
    return service.get_restaurant_info(item_id)


@mcp.tool()
def recommend_by_vibe(vibe: str, limit: int = 5) -> list[dict]:
    """Recommend restaurants whose vibe or environment matches a phrase."""
    return service.recommend_by_vibe(vibe, limit)


@mcp.tool()
def get_review(item_id: int) -> list[dict]:
    """Get reviews associated with a restaurant item ID."""
    return service.get_review(item_id)


def main() -> None:
    """Run this MCP server over stdio for a local MCP host."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
