export type UserPreferences = {
  defaultModel?: string;
  theme?: 'light' | 'dark' | 'system';
  language?: string;
  [key: string]: any;
};

export type User = {
  id: string;
  name: string;
  email: string;
  emailVerified: boolean;
  password?: string;
  image?: string;
  preferences: UserPreferences;
  createdAt: Date;
  updatedAt: Date;
};