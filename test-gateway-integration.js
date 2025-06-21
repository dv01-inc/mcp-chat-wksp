// Test script to verify gateway integration
const axios = require('axios');

const GATEWAY_URL = 'http://localhost:8002/api';
const CHAT_APP_URL = 'http://localhost:4200/api';
const MOCK_TOKEN = 'mock-token';

async function testGatewayIntegration() {
  console.log('🧪 Testing Gateway Integration...\n');
  
  try {
    // Test 1: Health Check
    console.log('1️⃣ Testing Gateway Health...');
    const health = await axios.get(`${GATEWAY_URL}/health`);
    console.log('✅ Health:', health.data);
    
    // Test 2: Environment Check
    console.log('\n2️⃣ Testing Gateway Environment...');
    const env = await axios.get(`${GATEWAY_URL}/test/env`);
    console.log('✅ Environment:', env.data);
    
    // Test 3: Apollo MCP Connection
    console.log('\n3️⃣ Testing Apollo MCP Connection...');
    const apollo = await axios.get(`${GATEWAY_URL}/test/apollo`);
    console.log('✅ Apollo:', apollo.data);
    
    // Test 4: Authenticated MCP Query
    console.log('\n4️⃣ Testing Authenticated MCP Query...');
    const query = await axios.post(`${GATEWAY_URL}/mcp/query`, {
      prompt: "Who are the astronauts currently in space?",
      serverUrl: "http://localhost:5000/mcp",
      modelName: "gpt-4"
    }, {
      headers: {
        'Authorization': `Bearer ${MOCK_TOKEN}`,
        'Content-Type': 'application/json'
      }
    });
    console.log('✅ MCP Query:', query.data);
    
    // Test 5: Chat App Integration
    console.log('\n5️⃣ Testing Chat App Gateway Integration...');
    try {
      const chatTest = await axios.get(`${CHAT_APP_URL}/test/gateway`);
      console.log('✅ Chat App Integration:', chatTest.data);
    } catch (chatError) {
      console.log('⚠️ Chat App Test (may not be running):', chatError.response?.data || chatError.message);
    }
    
    // Test 6: Chat App MCP Query
    console.log('\n6️⃣ Testing Chat App MCP Query...');
    try {
      const chatQuery = await axios.post(`${CHAT_APP_URL}/test/gateway`, {
        prompt: "Test query from integration script",
        serverUrl: "http://localhost:5000/mcp"
      });
      console.log('✅ Chat App MCP Query:', chatQuery.data);
    } catch (chatQueryError) {
      console.log('⚠️ Chat App Query (may not be running):', chatQueryError.response?.data || chatQueryError.message);
    }
    
    console.log('\n🎉 Gateway Integration Test Complete!');
    
  } catch (error) {
    console.error('❌ Error:', error.response?.data || error.message);
  }
}

testGatewayIntegration();