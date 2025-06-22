export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    // MCP initialization disabled - using gateway-only architecture
    // All MCP operations are handled by the MCP Gateway
    console.log("Gateway-only mode: Skipping local MCP manager initialization");
  }
}
