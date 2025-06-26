import { and, desc, eq } from "drizzle-orm";
import { db } from "../connection.js";
import {
  ChatMessageSchema,
  ChatThreadSchema,
  ProjectSchema,
  UserSchema,
} from "../schema.js";

export interface CreateThreadData {
  title: string;
  userId: string;
  projectId?: string;
}

export interface CreateMessageData {
  threadId: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  userId: string;
  toolInvocations?: any[];
}

export interface CreateProjectData {
  name: string;
  userId: string;
  instructions?: any;
}

export const chatRepository = {
  async createThread(data: CreateThreadData) {
    const [result] = await db
      .insert(ChatThreadSchema)
      .values({
        title: data.title,
        userId: data.userId,
        ...(data.projectId && { projectId: data.projectId }),
      })
      .returning();
    return result;
  },

  async getThread(id: string) {
    const [result] = await db
      .select()
      .from(ChatThreadSchema)
      .where(eq(ChatThreadSchema.id, id));
    return result || null;
  },

  async getThreadsByUserId(userId: string, projectId?: string) {
    let query = db
      .select()
      .from(ChatThreadSchema)
      .where(eq(ChatThreadSchema.userId, userId));

    if (projectId) {
      query = db
        .select()
        .from(ChatThreadSchema)
        .where(and(
          eq(ChatThreadSchema.userId, userId),
          eq(ChatThreadSchema.projectId, projectId)
        ));
    }

    return await query.orderBy(desc(ChatThreadSchema.createdAt));
  },

  async getMessagesByThreadId(threadId: string) {
    return await db
      .select()
      .from(ChatMessageSchema)
      .where(eq(ChatMessageSchema.threadId, threadId))
      .orderBy(ChatMessageSchema.createdAt);
  },

  async createMessage(data: CreateMessageData) {
    const values: any = {
      id: Date.now().toString(),
      threadId: data.threadId,
      role: data.role,
      parts: [{ type: 'text', text: data.content }],
    };
    
    // Add optional fields if they exist in schema
    if (ChatMessageSchema.attachments) values.attachments = [];
    if (ChatMessageSchema.annotations) values.annotations = data.toolInvocations || [];
    if (ChatMessageSchema.model) values.model = 'chat-api';

    const [result] = await db
      .insert(ChatMessageSchema)
      .values(values)
      .returning();
    return result;
  },

  async deleteMessage(id: string) {
    await db.delete(ChatMessageSchema).where(eq(ChatMessageSchema.id, id));
  },

  async updateThreadTitle(id: string, title: string) {
    await db
      .update(ChatThreadSchema)
      .set({ title })
      .where(eq(ChatThreadSchema.id, id));
  },

  async deleteThread(id: string) {
    await db.delete(ChatThreadSchema).where(eq(ChatThreadSchema.id, id));
  },

  async getProjects(userId: string) {
    return await db
      .select()
      .from(ProjectSchema)
      .where(eq(ProjectSchema.userId, userId))
      .orderBy(desc(ProjectSchema.createdAt));
  },

  async createProject(data: CreateProjectData) {
    const [result] = await db
      .insert(ProjectSchema)
      .values({
        name: data.name,
        userId: data.userId,
        ...(data.instructions && { instructions: data.instructions }),
      })
      .returning();
    return result;
  },

  async getProject(id: string) {
    const [result] = await db
      .select()
      .from(ProjectSchema)
      .where(eq(ProjectSchema.id, id));
    return result || null;
  },

  async updateProject(id: string, data: Partial<CreateProjectData>) {
    await db
      .update(ProjectSchema)
      .set(data)
      .where(eq(ProjectSchema.id, id));
  },

  async deleteProject(id: string) {
    await db.delete(ProjectSchema).where(eq(ProjectSchema.id, id));
  },
};