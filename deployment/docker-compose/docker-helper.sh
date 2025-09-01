#!/bin/bash

# Docker development helper script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Default values
COMMAND=""
ENVIRONMENT="development"
VERSION="latest"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        build)
            COMMAND="build"
            shift
            ;;
        up)
            COMMAND="up"
            shift
            ;;
        down)
            COMMAND="down"
            shift
            ;;
        logs)
            COMMAND="logs"
            shift
            ;;
        test)
            COMMAND="test"
            shift
            ;;
        shell)
            COMMAND="shell"
            shift
            ;;
        clean)
            COMMAND="clean"
            shift
            ;;
        --prod)
            ENVIRONMENT="production"
            shift
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        -h|--help)
            cat << EOF
Docker Helper Script for Web Scraper

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    build       Build the Docker image
    up          Start the services
    down        Stop the services
    logs        Show logs from running containers
    test        Run tests in Docker container
    shell       Open a shell in the web-scraper container
    clean       Remove all containers, images, and volumes

Options:
    --prod      Use production configuration
    --version   Specify image version (default: latest)
    -h, --help  Show this help message

Examples:
    $0 build                    # Build development image
    $0 up                       # Start development environment
    $0 up --prod               # Start production environment
    $0 test                    # Run tests in container
    $0 shell                   # Open shell in running container
    $0 logs                    # Show container logs
    $0 clean                   # Clean up everything

EOF
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information."
            exit 1
            ;;
    esac
done

# Set compose file based on environment
if [[ "$ENVIRONMENT" == "production" ]]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    print_status "Using production configuration"
else
    COMPOSE_FILE="docker-compose.yml"
    print_status "Using development configuration"
fi

# Execute commands
case $COMMAND in
    build)
        print_status "Building Docker image..."
        docker build -f ../../Dockerfile -t web-scraper:$VERSION ../../
        print_success "Image built successfully: web-scraper:$VERSION"
        ;;
    
    up)
        print_status "Starting services with $COMPOSE_FILE..."
        docker-compose -f $COMPOSE_FILE up -d
        print_success "Services started successfully"
        print_status "Available services:"
        docker-compose -f $COMPOSE_FILE ps
        ;;
    
    down)
        print_status "Stopping services..."
        docker-compose -f $COMPOSE_FILE down
        print_success "Services stopped successfully"
        ;;
    
    logs)
        print_status "Showing logs..."
        docker-compose -f $COMPOSE_FILE logs -f
        ;;
    
    test)
        print_status "Running tests in Docker container..."
        docker run --rm -v $(pwd)/../../:/app -w /app web-scraper:$VERSION \
            bash -c "pixi install && pixi run test"
        print_success "Tests completed"
        ;;
    
    shell)
        print_status "Opening shell in web-scraper container..."
        if docker-compose -f $COMPOSE_FILE ps web-scraper | grep -q "Up"; then
            docker-compose -f $COMPOSE_FILE exec web-scraper bash
        else
            print_warning "Container not running. Starting temporary container..."
            docker run --rm -it -v $(pwd)/../../:/app -w /app web-scraper:$VERSION bash
        fi
        ;;
    
    clean)
        print_warning "This will remove ALL containers, images, and volumes related to this project"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Cleaning up..."
            docker-compose -f docker-compose.yml down -v --remove-orphans 2>/dev/null || true
            docker-compose -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
            docker rmi web-scraper:$VERSION 2>/dev/null || true
            docker system prune -f
            print_success "Cleanup completed"
        else
            print_status "Cleanup cancelled"
        fi
        ;;
    
    "")
        print_error "No command specified"
        echo "Use -h or --help for usage information."
        exit 1
        ;;
    
    *)
        print_error "Unknown command: $COMMAND"
        echo "Use -h or --help for usage information."
        exit 1
        ;;
esac