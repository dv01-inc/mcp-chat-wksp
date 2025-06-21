import { NextRequest, NextResponse } from "next/server";

/**
 * Test endpoint to verify MCP Gateway integration
 */
export async function GET(request: NextRequest) {
  try {
    const gatewayUrl = process.env.NEXT_PUBLIC_MCP_GATEWAY_URL || 'http://localhost:8002/api';
    const authToken = process.env.NEXT_PUBLIC_MCP_AUTH_TOKEN || 'mock-token';
    
    // Test gateway health
    const healthResponse = await fetch(`${gatewayUrl}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!healthResponse.ok) {
      throw new Error(`Gateway health check failed: ${healthResponse.status}`);
    }
    
    const healthData = await healthResponse.json();
    
    // Test authenticated endpoint
    const queryResponse = await fetch(`${gatewayUrl}/mcp/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
      },
      body: JSON.stringify({
        prompt: "Hello from chat app! Can you tell me what tools are available?",
        serverUrl: "http://localhost:5000/mcp",
        modelName: "gpt-4",
      }),
    });
    
    let queryData = null;
    let queryError = null;
    
    if (queryResponse.ok) {
      queryData = await queryResponse.json();
    } else {
      queryError = `Query failed: ${queryResponse.status} ${queryResponse.statusText}`;
    }
    
    return NextResponse.json({
      status: "success",
      gateway: {
        url: gatewayUrl,
        health: healthData,
        authenticated_query: queryData,
        query_error: queryError,
      },
      environment: {
        use_gateway: process.env.NEXT_PUBLIC_USE_MCP_GATEWAY,
        gateway_url: process.env.NEXT_PUBLIC_MCP_GATEWAY_URL,
        has_auth_token: !!process.env.NEXT_PUBLIC_MCP_AUTH_TOKEN,
      },
      message: "Gateway integration test completed",
    });
    
  } catch (error) {
    return NextResponse.json({
      status: "error",
      error: error instanceof Error ? error.message : String(error),
      environment: {
        use_gateway: process.env.NEXT_PUBLIC_USE_MCP_GATEWAY,
        gateway_url: process.env.NEXT_PUBLIC_MCP_GATEWAY_URL,
        has_auth_token: !!process.env.NEXT_PUBLIC_MCP_AUTH_TOKEN,
      },
      message: "Gateway integration test failed",
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const { serverUrl, prompt } = await request.json();
    
    const gatewayUrl = process.env.NEXT_PUBLIC_MCP_GATEWAY_URL || 'http://localhost:8002/api';
    const authToken = process.env.NEXT_PUBLIC_MCP_AUTH_TOKEN || 'mock-token';
    
    // Test specific MCP query through gateway
    const response = await fetch(`${gatewayUrl}/mcp/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
      },
      body: JSON.stringify({
        prompt: prompt || "Test query from chat app",
        serverUrl: serverUrl || "http://localhost:5000/mcp",
        modelName: "gpt-4",
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Gateway request failed: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    
    return NextResponse.json({
      status: "success",
      result: data,
      message: "MCP query through gateway successful",
    });
    
  } catch (error) {
    return NextResponse.json({
      status: "error",
      error: error instanceof Error ? error.message : String(error),
      message: "MCP query through gateway failed",
    }, { status: 500 });
  }
}