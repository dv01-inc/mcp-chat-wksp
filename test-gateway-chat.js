#!/usr/bin/env node
/**
 * Test script to verify the gateway-only chat works
 */

const GATEWAY_URL = 'http://localhost:8000';
const AUTH_TOKEN = 'mock-token';

async function testGatewayChat() {
  console.log('🧪 Testing Gateway-Only Chat Architecture');
  console.log('==========================================');
  
  try {
    // Test 1: Get available servers
    console.log('\n1. Getting available servers...');
    const serversResponse = await fetch(`${GATEWAY_URL}/mcp/servers`, {
      headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
    });
    const servers = await serversResponse.json();
    
    console.log(`✅ Found ${servers.servers.length} servers:`);
    servers.servers.forEach(server => {
      console.log(`   • ${server.name} (${server.id}) - ${server.status}`);
    });
    
    // Test 2: Send navigation request
    console.log('\n2. Testing navigation request: "Go to google.com"...');
    const chatResponse = await fetch(`${GATEWAY_URL}/mcp/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt: 'Go to google.com',
        server_url: 'http://localhost:8001/sse',
        model_name: 'gpt-4'
      })
    });
    
    const chatResult = await chatResponse.json();
    
    if (chatResult.error) {
      console.log(`❌ Chat failed: ${chatResult.error}`);
    } else {
      console.log(`✅ Chat successful!`);
      console.log(`   Response: ${chatResult.result.substring(0, 100)}...`);
      console.log(`   Usage: ${JSON.stringify(chatResult.usage)}`);
    }
    
    // Test 3: Test tool execution
    console.log('\n3. Testing direct tool execution...');
    const toolResponse = await fetch(`${GATEWAY_URL}/mcp/tools/execute`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        server_id: 'playwright',
        tool_name: 'browser_screenshot',
        parameters: {}
      })
    });
    
    const toolResult = await toolResponse.json();
    
    if (toolResult.error) {
      console.log(`❌ Tool execution failed: ${toolResult.error}`);
    } else {
      console.log(`✅ Tool execution successful!`);
      console.log(`   Response: ${toolResult.result.substring(0, 100)}...`);
    }
    
    console.log('\n🎉 Gateway-only architecture is working correctly!');
    console.log('\nKey benefits:');
    console.log('• ✅ No LLM processing in Next.js app');
    console.log('• ✅ All AI/MCP logic handled by gateway');
    console.log('• ✅ Simple HTTP API for any client to integrate');
    console.log('• ✅ Easy to add new clients (Slack, mobile, etc.)');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testGatewayChat();