declare namespace Express {
  interface Request {
    user?: {
      id: string;
      email: string;
      name: string;
    };
  }
}