from mcp.server.fastmcp import FastMCP

mcp = FastMCP("sample")

@mcp.tool()
async def get_service_status() -> str:
    """Check the status of the sample service."""
    return "Sample service is running and healthy!"

@mcp.tool()
async def echo_message(message: str) -> str:
    """Echo back the provided message."""
    return f"Service received: {message}"

if __name__ == "__main__":
    mcp.run()
