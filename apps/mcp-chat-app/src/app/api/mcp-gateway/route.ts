/**
 * Next.js API routes for MCP Gateway
 * Simple proxy to the MCP Gateway for any client interface
 */

import { NextRequest, NextResponse } from 'next/server';

const GATEWAY_URL = process.env.NEXT_PUBLIC_MCP_GATEWAY_URL || 'http://localhost:8000';
const AUTH_TOKEN = process.env.NEXT_PUBLIC_MCP_AUTH_TOKEN || 'mock-token';

async function proxyToGateway(
  endpoint: string,
  method: string,
  body?: any,
  authToken?: string
) {
  const url = `${GATEWAY_URL}${endpoint}`;
  
  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken || AUTH_TOKEN}`,
    },
  };

  if (body && method !== 'GET') {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url, options);
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Gateway request failed: ${response.status} ${response.statusText} - ${errorText}`);
  }

  return response.json();
}

// GET /api/mcp-gateway/servers - List available servers
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const endpoint = searchParams.get('endpoint') || '/mcp/servers';
    const authToken = request.headers.get('authorization')?.replace('Bearer ', '');
    
    const result = await proxyToGateway(endpoint, 'GET', undefined, authToken);
    
    return NextResponse.json(result);
  } catch (error) {
    console.error('Gateway proxy error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Gateway request failed' },
      { status: 500 }
    );
  }
}

// POST /api/mcp-gateway - Execute tools, queries, or chat
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { searchParams } = new URL(request.url);
    const endpoint = searchParams.get('endpoint') || '/mcp/query';
    const authToken = request.headers.get('authorization')?.replace('Bearer ', '');
    
    const result = await proxyToGateway(endpoint, 'POST', body, authToken);
    
    return NextResponse.json(result);
  } catch (error) {
    console.error('Gateway proxy error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Gateway request failed' },
      { status: 500 }
    );
  }
}

// DELETE /api/mcp-gateway - Disconnect servers
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const endpoint = searchParams.get('endpoint') || '/mcp/servers/unknown';
    const authToken = request.headers.get('authorization')?.replace('Bearer ', '');
    
    const result = await proxyToGateway(endpoint, 'DELETE', undefined, authToken);
    
    return NextResponse.json(result);
  } catch (error) {
    console.error('Gateway proxy error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Gateway request failed' },
      { status: 500 }
    );
  }
}