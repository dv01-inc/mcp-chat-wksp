import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { config } from './config/env.js';
import { errorHandler } from './middleware/error-handler.js';
import { requireAuth } from './middleware/auth.js';
import { authRoutes } from './routes/auth.js';
import { chatRoutes } from './routes/chat.js';
import { mcpRoutes } from './routes/mcp.js';
import { threadRoutes } from './routes/thread.js';
import { userRoutes } from './routes/user.js';

const app = express();

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN?.split(',') || ['http://localhost:3000'],
  credentials: true
}));

// Logging
app.use(morgan('combined'));

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'chat-api', timestamp: new Date().toISOString() });
});

// API routes
app.use('/api/auth', authRoutes);
app.use('/api/chat', requireAuth, chatRoutes);
app.use('/api/mcp', requireAuth, mcpRoutes);
app.use('/api/thread', requireAuth, threadRoutes);
app.use('/api/user', requireAuth, userRoutes);

// Error handling
app.use(errorHandler);

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

const port = config.PORT || 3001;

app.listen(port, () => {
  console.log(`🚀 Chat API server running on port ${port}`);
  console.log(`📡 Health check: http://localhost:${port}/health`);
});

export default app;