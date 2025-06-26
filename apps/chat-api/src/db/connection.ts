import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import { config } from '../config/env.js';
import * as schema from './schema.js';

// Create connection
const connectionString = config.DATABASE_URL || 'postgresql://postgres:password@localhost:5432/chatdb';

// Create postgres client
const client = postgres(connectionString, {
  prepare: false,
  max: 10,
});

// Create drizzle instance
export const db = drizzle(client, { schema });

// Helper to close connection
export const closeConnection = async () => {
  await client.end();
};

export type Database = typeof db;