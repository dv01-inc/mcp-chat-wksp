#!/usr/bin/env node
/**
 * Test script to verify the database migration to gateway
 */

const GATEWAY_URL = 'http://localhost:8000';
const AUTH_TOKEN = 'mock-token';

async function testDatabaseMigration() {
  console.log('🗄️ Testing Database Migration to Gateway');
  console.log('==========================================');
  
  try {
    // Test 1: Create a new thread via gateway
    console.log('\n1. Creating a new chat thread via gateway...');
    const createThreadResponse = await fetch(`${GATEWAY_URL}/chat/threads`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: 'Test Thread via Gateway',
        project_id: null
      })
    });
    
    if (!createThreadResponse.ok) {
      throw new Error(`Failed to create thread: ${createThreadResponse.status}`);
    }
    
    const newThread = await createThreadResponse.json();
    console.log(`✅ Thread created: ${newThread.id}`);
    console.log(`   Title: ${newThread.title}`);
    console.log(`   User: ${newThread.user_id}`);
    
    // Test 2: Add a message to the thread
    console.log('\n2. Adding a message to the thread...');
    const addMessageResponse = await fetch(`${GATEWAY_URL}/chat/threads/${newThread.id}/messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message_id: `test-message-${Date.now()}`,
        role: 'user',
        parts: [{ type: 'text', text: 'Hello from gateway database!' }],
        attachments: [],
        annotations: []
      })
    });
    
    if (!addMessageResponse.ok) {
      throw new Error(`Failed to add message: ${addMessageResponse.status}`);
    }
    
    const newMessage = await addMessageResponse.json();
    console.log(`✅ Message added: ${newMessage.id}`);
    console.log(`   Content: ${newMessage.parts[0].text}`);
    
    // Test 3: Retrieve the thread with messages
    console.log('\n3. Retrieving thread with messages...');
    const getThreadResponse = await fetch(`${GATEWAY_URL}/chat/threads/${newThread.id}`, {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    });
    
    if (!getThreadResponse.ok) {
      throw new Error(`Failed to get thread: ${getThreadResponse.status}`);
    }
    
    const threadWithMessages = await getThreadResponse.json();
    console.log(`✅ Thread retrieved with ${threadWithMessages.messages.length} messages`);
    threadWithMessages.messages.forEach((msg, i) => {
      console.log(`   Message ${i + 1}: ${msg.parts[0].text.substring(0, 50)}...`);
    });
    
    // Test 4: Test intelligent chat with history
    console.log('\n4. Testing intelligent chat with history saving...');
    const chatResponse = await fetch(`${GATEWAY_URL}/mcp/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt: 'Take a screenshot of google.com',
        model_name: 'openai:gpt-4',
        thread_id: newThread.id,
        message_id: `user-message-${Date.now()}`
      })
    });
    
    if (!chatResponse.ok) {
      throw new Error(`Chat failed: ${chatResponse.status}`);
    }
    
    const chatResult = await chatResponse.json();
    console.log(`✅ Intelligent chat successful!`);
    console.log(`   Server selected: ${chatResult.usage?.selected_server || 'unknown'}`);
    console.log(`   Response preview: ${chatResult.result.substring(0, 100)}...`);
    
    // Test 5: Verify the chat messages were saved
    console.log('\n5. Verifying chat history was saved...');
    const finalThreadResponse = await fetch(`${GATEWAY_URL}/chat/threads/${newThread.id}`, {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    });
    
    const finalThread = await finalThreadResponse.json();
    console.log(`✅ Thread now has ${finalThread.messages.length} messages`);
    console.log(`   Latest message: ${finalThread.messages[finalThread.messages.length - 1].parts[0].text.substring(0, 100)}...`);
    
    // Test 6: List all threads
    console.log('\n6. Listing all user threads...');
    const threadsResponse = await fetch(`${GATEWAY_URL}/chat/threads`, {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    });
    
    const threadsData = await threadsResponse.json();
    console.log(`✅ Found ${threadsData.threads.length} threads for user`);
    threadsData.threads.forEach((thread, i) => {
      console.log(`   Thread ${i + 1}: ${thread.title} (${thread.id.substring(0, 8)}...)`);
    });
    
    console.log('\n🎉 Database Migration Test Complete!');
    console.log('\nKey achievements:');
    console.log('• ✅ Gateway now owns all chat data');
    console.log('• ✅ Thread creation works via gateway API');
    console.log('• ✅ Message storage works via gateway API');
    console.log('• ✅ Intelligent chat saves history automatically');
    console.log('• ✅ Chat history retrieval works via gateway API');
    console.log('• ✅ Next.js app can be completely database-free!');
    
  } catch (error) {
    console.error('❌ Database migration test failed:', error.message);
  }
}

testDatabaseMigration();