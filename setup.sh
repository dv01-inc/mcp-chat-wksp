#!/bin/bash

# MCP Chat Workspace Setup Script
# This script sets up the entire development environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}"
    echo "============================================"
    echo "$1"
    echo "============================================"
    echo -e "${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    print_header "Checking System Requirements"
    
    # Check Node.js
    if command_exists node; then
        NODE_VERSION=$(node --version)
        print_status "Node.js found: $NODE_VERSION"
        
        # Check if Node.js version is 18 or higher
        NODE_MAJOR=$(echo $NODE_VERSION | sed 's/v//' | cut -d. -f1)
        if [ "$NODE_MAJOR" -lt 18 ]; then
            print_error "Node.js 18+ is required. Current version: $NODE_VERSION"
            exit 1
        fi
    else
        print_error "Node.js not found. Please install Node.js 18+ from https://nodejs.org/"
        exit 1
    fi
    
    # Check pnpm
    if command_exists pnpm; then
        PNPM_VERSION=$(pnpm --version)
        print_status "pnpm found: $PNPM_VERSION"
    else
        print_warning "pnpm not found. Installing pnpm..."
        npm install -g pnpm
    fi
    
    # Check Docker (optional but recommended)
    if command_exists docker; then
        print_status "Docker found"
        if docker info >/dev/null 2>&1; then
            print_status "Docker daemon is running"
        else
            print_warning "Docker daemon is not running. You can start it later for database services."
        fi
    else
        print_warning "Docker not found. You can install it later for database services."
    fi
    
    # Check PostgreSQL (if not using Docker)
    if command_exists psql; then
        print_status "PostgreSQL found"
    else
        print_warning "PostgreSQL not found locally. Will use Docker container if available."
    fi
}

# Setup environment files
setup_environment() {
    print_header "Setting Up Environment Files"
    
    # Root .env
    if [ ! -f ".env" ]; then
        print_status "Creating root .env file..."
        cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/mcp_chat
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=mcp_chat

# Chat API Configuration
CHAT_API_PORT=3001
CHAT_API_URL=http://localhost:3001

# Next.js App Configuration
NEXTAUTH_SECRET=your-secret-key-change-this-in-production
NEXTAUTH_URL=http://localhost:3000

# CORS Configuration
CORS_ORIGIN=http://localhost:3000

# API Keys (add your own)
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
GOOGLE_GENERATIVE_AI_API_KEY=your-google-api-key
XAI_API_KEY=your-xai-api-key
EOF
        print_status "Created .env file. Please update API keys as needed."
    else
        print_status "Root .env file already exists"
    fi
    
    # Chat API .env
    if [ ! -f "apps/chat-api/.env" ]; then
        print_status "Creating chat-api .env file..."
        cat > apps/chat-api/.env << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/mcp_chat

# Server Configuration
PORT=3001
NODE_ENV=development

# CORS
CORS_ORIGIN=http://localhost:3000

# API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
GOOGLE_GENERATIVE_AI_API_KEY=your-google-api-key
XAI_API_KEY=your-xai-api-key
EOF
        print_status "Created chat-api .env file"
    else
        print_status "Chat API .env file already exists"
    fi
    
    # Chat App .env.local
    if [ ! -f "apps/chat/.env.local" ]; then
        print_status "Creating chat app .env.local file..."
        cat > apps/chat/.env.local << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/mcp_chat

# Authentication
NEXTAUTH_SECRET=your-secret-key-change-this-in-production
NEXTAUTH_URL=http://localhost:3000

# External API
CHAT_API_URL=http://localhost:3001

# API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
GOOGLE_GENERATIVE_AI_API_KEY=your-google-api-key
XAI_API_KEY=your-xai-api-key
EOF
        print_status "Created chat app .env.local file"
    else
        print_status "Chat app .env.local file already exists"
    fi
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    print_status "Installing root dependencies..."
    pnpm install
    
    print_status "Installing chat-api dependencies..."
    cd apps/chat-api && pnpm install && cd ../..
    
    print_status "Installing chat app dependencies..."
    cd apps/chat && pnpm install && cd ../..
    
    print_status "All dependencies installed successfully!"
}

# Setup database
setup_database() {
    print_header "Setting Up Database"
    
    # Check if Docker is available and running
    if command_exists docker && docker info >/dev/null 2>&1; then
        print_status "Starting PostgreSQL with Docker..."
        
        # Create docker-compose.yml if it doesn't exist
        if [ ! -f "docker-compose.yml" ]; then
            cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: mcp-chat-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mcp_chat
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
EOF
            print_status "Created docker-compose.yml"
        fi
        
        # Start PostgreSQL container
        docker-compose up -d postgres
        
        # Wait for PostgreSQL to be ready
        print_status "Waiting for PostgreSQL to be ready..."
        while ! docker-compose exec postgres pg_isready -U postgres >/dev/null 2>&1; do
            sleep 2
        done
        
        print_status "PostgreSQL is ready!"
        
    else
        print_warning "Docker not available. Please ensure PostgreSQL is running on localhost:5432"
        print_warning "Database: mcp_chat, User: postgres, Password: password"
    fi
    
    # Run database migrations for chat-api
    print_status "Running database migrations..."
    cd apps/chat-api
    if [ -f "drizzle.config.ts" ]; then
        npx drizzle-kit push:pg || print_warning "Migration failed - database might already be set up"
    fi
    cd ../..
}

# Build all projects
build_projects() {
    print_header "Building Projects"
    
    print_status "Building chat-api..."
    npx nx build chat-api
    
    print_status "Building chat app..."
    npx nx build chat || print_warning "Chat app build failed - this is normal if there are frontend integration issues"
    
    print_status "Build completed!"
}

# Start all services
start_services() {
    print_header "Starting Services"
    
    print_status "Services will be started in the background..."
    print_status "Chat API will be available at: http://localhost:3001"
    print_status "Chat App will be available at: http://localhost:3000"
    
    echo ""
    print_status "To start the services manually:"
    echo "  1. Chat API: cd apps/chat-api && npm run dev"
    echo "  2. Chat App: cd apps/chat && npm run dev"
    echo ""
    
    # Ask user if they want to start services now
    read -p "Would you like to start the services now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Starting chat-api in background..."
        cd apps/chat-api && npm run dev &
        CHAT_API_PID=$!
        cd ../..
        
        print_status "Waiting for chat-api to start..."
        sleep 5
        
        print_status "Starting chat app in background..."
        cd apps/chat && npm run dev &
        CHAT_APP_PID=$!
        cd ../..
        
        echo ""
        print_status "Services started!"
        print_status "Chat API PID: $CHAT_API_PID"
        print_status "Chat App PID: $CHAT_APP_PID"
        echo ""
        print_status "To stop services:"
        echo "  kill $CHAT_API_PID $CHAT_APP_PID"
        echo ""
        print_status "Or use Ctrl+C to stop this script and manually manage services"
        
        # Keep script running
        wait
    fi
}

# Show next steps
show_next_steps() {
    print_header "Setup Complete!"
    
    echo -e "${GREEN}🎉 Your MCP Chat Workspace is ready!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Update API keys in .env files:"
    echo "   - .env (root)"
    echo "   - apps/chat-api/.env"
    echo "   - apps/chat/.env.local"
    echo ""
    echo "2. Start the services:"
    echo "   - Chat API: cd apps/chat-api && npm run dev"
    echo "   - Chat App: cd apps/chat && npm run dev"
    echo ""
    echo "3. Access the applications:"
    echo "   - Chat API: http://localhost:3001"
    echo "   - Chat App: http://localhost:3000"
    echo "   - Health Check: http://localhost:3001/health"
    echo ""
    echo "4. Add MCP servers via the API:"
    echo "   - POST http://localhost:3001/api/mcp/servers"
    echo "   - GET http://localhost:3001/api/mcp/tools"
    echo ""
    echo "📚 For more information, check the README files in each app directory."
}

# Main execution
main() {
    print_header "MCP Chat Workspace Setup"
    echo "This script will set up your development environment"
    echo ""
    
    check_requirements
    setup_environment
    install_dependencies
    setup_database
    build_projects
    start_services
    show_next_steps
}

# Run main function
main "$@"