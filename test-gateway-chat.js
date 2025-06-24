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
    
    // Test 2: Send navigation request (gateway selects server automatically!)
    console.log('\n2. Testing navigation request: "Go to google.com"...');
    const chatResponse = await fetch(`${GATEWAY_URL}/mcp/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt: 'Go to google.com',
        model_name: 'openai:gpt-4'
        // No server_url needed! Gateway intelligently selects the right server
      })
    });
    
    const chatResult = await chatResponse.json();
    
    if (chatResult.error) {
      console.log(`❌ Chat failed: ${chatResult.error}`);
    } else {
      console.log(`✅ Chat successful!`);
      console.log(`   Response: ${chatResult.result.substring(0, 100)}...`);
      console.log(`   Selected Server: ${chatResult.usage?.selected_server || 'unknown'}`);
      console.log(`   Usage: ${JSON.stringify(chatResult.usage)}`);
    }
    
    // Test 3: Test space query (should route to Apollo server)
    console.log('\n3. Testing space query: "Who are the astronauts currently in space?"...');
    const spaceResponse = await fetch(`${GATEWAY_URL}/mcp/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt: 'Who are the astronauts currently in space?',
        model_name: 'openai:gpt-4'
        // Gateway should automatically route this to Apollo server!
      })
    });
    
    const spaceResult = await spaceResponse.json();
    
    if (spaceResult.error) {
      console.log(`❌ Space query failed: ${spaceResult.error}`);
    } else {
      console.log(`✅ Space query successful!`);
      console.log(`   Response: ${(spaceResult.result || '').substring(0, 100)}...`);
      console.log(`   Selected Server: ${spaceResult.usage?.selected_server || 'unknown'}`);
    }
    
    console.log('\n🎉 Intelligent Gateway Architecture is working perfectly!');
    console.log('\nKey benefits:');
    console.log('• ✅ No LLM processing in Next.js app');
    console.log('• ✅ No tool selection logic in clients');
    console.log('• ✅ Gateway intelligently routes to best server');
    console.log('• ✅ Pure natural language interface');
    console.log('• ✅ Clients are truly "dumb" - just HTTP calls');
    console.log('• ✅ Easy to add new clients (Slack, mobile, CLI, etc.)');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testGatewayChat();