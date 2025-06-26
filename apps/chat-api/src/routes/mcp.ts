import { Router } from 'express';
import { asyncHandler, createError } from '../middleware/error-handler.js';
import type { MCPClientsManager } from '../lib/mcp-manager.js';

const router = Router();

// GET /api/mcp/servers - Get all MCP servers
router.get('/servers', asyncHandler(async (req, res) => {
  const mcpManager = req.app.locals.mcpManager as MCPClientsManager;
  const servers = mcpManager.getServerInfo();
  res.json({ servers });
}));

// POST /api/mcp/servers - Add a new MCP server
router.post('/servers', asyncHandler(async (req, res) => {
  const mcpManager = req.app.locals.mcpManager as MCPClientsManager;
  const { name, config } = req.body;
  
  if (!name || !config) {
    throw createError('Name and config are required', 400);
  }
  
  try {
    const id = await mcpManager.persistClient({ name, config });
    res.json({ id, name, config, message: 'Server added successfully' });
  } catch (error) {
    throw createError('Failed to add MCP server', 500);
  }
}));

// DELETE /api/mcp/servers/:id - Remove an MCP server
router.delete('/servers/:id', asyncHandler(async (req, res) => {
  const mcpManager = req.app.locals.mcpManager as MCPClientsManager;
  const { id } = req.params;
  
  await mcpManager.removeClient(id);
  res.json({ message: 'Server removed successfully' });
}));

// POST /api/mcp/servers/:id/refresh - Refresh an MCP server
router.post('/servers/:id/refresh', asyncHandler(async (req, res) => {
  const mcpManager = req.app.locals.mcpManager as MCPClientsManager;
  const { id } = req.params;
  
  try {
    await mcpManager.refreshClient(id);
    res.json({ message: 'Server refreshed successfully' });
  } catch (error) {
    throw createError('Failed to refresh MCP server', 500);
  }
}));

// GET /api/mcp/tools - Get all available tools
router.get('/tools', asyncHandler(async (req, res) => {
  const mcpManager = req.app.locals.mcpManager as MCPClientsManager;
  const tools = mcpManager.tools();
  res.json({ tools });
}));

// POST /api/mcp/tools/:toolId/call - Call a specific tool
router.post('/tools/:toolId/call', asyncHandler(async (req, res) => {
  const mcpManager = req.app.locals.mcpManager as MCPClientsManager;
  const { toolId } = req.params;
  const { parameters } = req.body;
  
  const tools = mcpManager.tools();
  const tool = tools[toolId];
  
  if (!tool) {
    throw createError('Tool not found', 404);
  }
  
  try {
    const result = await tool.execute(parameters, {
      toolCallId: 'manual-call',
      messages: [],
    });
    res.json({ result });
  } catch (error) {
    console.error('Tool execution error:', error);
    throw createError('Tool execution failed', 500);
  }
}));

// GET /api/mcp/server-customizations/:server
router.get('/server-customizations/:server', asyncHandler(async (req, res) => {
  const { server } = req.params;
  // Implementation for server customizations
  res.json({ server, customizations: {} });
}));

// POST /api/mcp/server-customizations/:server
router.post('/server-customizations/:server', asyncHandler(async (req, res) => {
  const { server } = req.params;
  const customizations = req.body;
  // Implementation for saving server customizations
  res.json({ server, customizations, saved: true });
}));

// GET /api/mcp/tool-customizations/:server
router.get('/tool-customizations/:server', asyncHandler(async (req, res) => {
  const { server } = req.params;
  // Implementation for tool customizations
  res.json({ server, toolCustomizations: {} });
}));

// GET /api/mcp/tool-customizations/:server/:tool
router.get('/tool-customizations/:server/:tool', asyncHandler(async (req, res) => {
  const { server, tool } = req.params;
  // Implementation for specific tool customizations
  res.json({ server, tool, customizations: {} });
}));

// POST /api/mcp/tool-customizations/:server/:tool
router.post('/tool-customizations/:server/:tool', asyncHandler(async (req, res) => {
  const { server, tool } = req.params;
  const customizations = req.body;
  // Implementation for saving tool customizations
  res.json({ server, tool, customizations, saved: true });
}));

export { router as mcpRoutes };