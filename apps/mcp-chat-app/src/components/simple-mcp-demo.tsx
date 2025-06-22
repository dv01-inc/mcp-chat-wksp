/**
 * Simple MCP Demo Component
 * Demonstrates the new "dumb client" architecture where the Next.js app
 * only handles UI, auth, and gateway communication
 */

'use client';

import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Loader2, Server, Tool } from 'lucide-react';
import useMCPGateway from '../hooks/use-mcp-gateway';

export function SimpleMCPDemo() {
  const {
    servers,
    loading,
    error,
    refreshServers,
    executeTool,
    query,
    getAllTools
  } = useMCPGateway();

  const [selectedServer, setSelectedServer] = useState<string>('');
  const [selectedTool, setSelectedTool] = useState<string>('');
  const [toolParams, setToolParams] = useState<string>('{}');
  const [queryText, setQueryText] = useState<string>('');
  const [results, setResults] = useState<any>(null);
  const [executing, setExecuting] = useState(false);

  const handleExecuteTool = async () => {
    if (!selectedServer || !selectedTool) return;

    setExecuting(true);
    try {
      let parameters: any = {};
      if (toolParams.trim()) {
        parameters = JSON.parse(toolParams);
      }

      const result = await executeTool({
        server_id: selectedServer,
        tool_name: selectedTool,
        parameters
      });

      setResults(result);
    } catch (err) {
      console.error('Tool execution failed:', err);
    } finally {
      setExecuting(false);
    }
  };

  const handleQuery = async () => {
    if (!selectedServer || !queryText.trim()) return;

    setExecuting(true);
    try {
      const server = servers.find(s => s.id === selectedServer);
      if (!server) return;

      const result = await query({
        prompt: queryText,
        server_url: server.server_url
      });

      setResults(result);
    } catch (err) {
      console.error('Query failed:', err);
    } finally {
      setExecuting(false);
    }
  };

  const allTools = getAllTools();

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Simple MCP Gateway Demo
          </CardTitle>
          <CardDescription>
            Demonstrating the new "dumb client" architecture - Pure gateway communication
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Server Discovery */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Available MCP Servers
            <Button 
              onClick={refreshServers} 
              disabled={loading}
              variant="outline"
              size="sm"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Refresh'}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="text-red-600 mb-4 p-3 bg-red-50 rounded">
              Error: {error}
            </div>
          )}
          
          <div className="grid gap-4 md:grid-cols-2">
            {servers.map((server) => (
              <Card 
                key={server.id} 
                className={`cursor-pointer transition-colors ${
                  selectedServer === server.id ? 'ring-2 ring-blue-500' : ''
                }`}
                onClick={() => setSelectedServer(server.id)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{server.name}</CardTitle>
                    <Badge variant={server.status === 'available' ? 'default' : 'secondary'}>
                      {server.status}
                    </Badge>
                  </div>
                  <CardDescription>{server.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="text-sm">
                      <strong>Transport:</strong> {server.transport}
                    </div>
                    <div className="text-sm">
                      <strong>Tools:</strong> {server.tools.length}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {server.capabilities.slice(0, 3).map((cap) => (
                        <Badge key={cap} variant="outline" className="text-xs">
                          {cap}
                        </Badge>
                      ))}
                      {server.capabilities.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{server.capabilities.length - 3} more
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Tool Execution */}
      {selectedServer && (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Tool className="h-5 w-5" />
                Execute Specific Tool
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Tool</label>
                <select 
                  className="w-full p-2 border rounded"
                  value={selectedTool}
                  onChange={(e) => setSelectedTool(e.target.value)}
                >
                  <option value="">Select a tool...</option>
                  {servers
                    .find(s => s.id === selectedServer)
                    ?.tools.map((tool) => (
                      <option key={tool} value={tool}>
                        {tool}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Parameters (JSON)
                </label>
                <Textarea
                  placeholder='{"url": "https://example.com"}'
                  value={toolParams}
                  onChange={(e) => setToolParams(e.target.value)}
                  className="font-mono text-sm"
                />
              </div>

              <Button 
                onClick={handleExecuteTool}
                disabled={!selectedTool || executing}
                className="w-full"
              >
                {executing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Execute Tool
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Natural Language Query</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Query</label>
                <Textarea
                  placeholder="Take a screenshot of google.com"
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                />
              </div>

              <Button 
                onClick={handleQuery}
                disabled={!queryText.trim() || executing}
                className="w-full"
              >
                {executing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Send Query
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Results */}
      {results && (
        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <strong>Response:</strong>
                <pre className="mt-2 p-3 bg-gray-50 rounded text-sm overflow-auto">
                  {results.result}
                </pre>
              </div>
              
              {results.usage && (
                <div>
                  <strong>Usage:</strong>
                  <pre className="mt-2 p-3 bg-gray-50 rounded text-sm">
                    {JSON.stringify(results.usage, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Available Tools Summary */}
      <Card>
        <CardHeader>
          <CardTitle>All Available Tools ({allTools.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-3 lg:grid-cols-4">
            {allTools.map(({ server, tool }) => (
              <div key={`${server.id}-${tool}`} className="p-2 bg-gray-50 rounded text-sm">
                <div className="font-medium">{tool}</div>
                <div className="text-gray-600 text-xs">{server.name}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}