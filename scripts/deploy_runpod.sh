#!/bin/bash

##########################################################################
# RunPod Serverless Deployment Script
# 
# This script automates the deployment process to RunPod Serverless
# 
# Usage:
#   ./deploy_runpod.sh [OPTIONS]
#
# Options:
#   --build              Build Docker image
#   --push               Push to Docker registry
#   --create-endpoint    Create RunPod endpoint
#   --test               Test deployment
#   --all                Execute all steps
#   --docker-registry    Docker registry (default: docker.io)
#   --docker-image       Docker image name (default: ivrimeet-runpod)
#   --docker-tag         Docker image tag (default: latest)
#   --help              Show this help message
#
# Examples:
#   ./deploy_runpod.sh --build --push
#   ./deploy_runpod.sh --all
#   ./deploy_runpod.sh --test
##########################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BUILD=false
PUSH=false
CREATE_ENDPOINT=false
TEST=false
DOCKER_REGISTRY="docker.io"
DOCKER_IMAGE="ivrimeet-runpod"
DOCKER_TAG="latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

show_help() {
    grep "^#" "$0" | grep -v "^#!/bin/bash" | sed 's/^# *//'
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker found: $(docker --version)"
}

check_requirements() {
    print_header "Checking Requirements"
    check_docker
    
    if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
        print_error "requirements.txt not found in $PROJECT_ROOT"
        exit 1
    fi
    print_success "requirements.txt found"
    
    if [ ! -f "$PROJECT_ROOT/Dockerfile.runpod_serverless" ]; then
        print_error "Dockerfile.runpod_serverless not found in $PROJECT_ROOT"
        exit 1
    fi
    print_success "Dockerfile.runpod_serverless found"
}

build_docker_image() {
    print_header "Building Docker Image"
    
    echo "Building: $DOCKER_REGISTRY/$DOCKER_IMAGE:$DOCKER_TAG"
    echo "Location: $PROJECT_ROOT"
    
    cd "$PROJECT_ROOT"
    docker build -f Dockerfile.runpod_serverless \
        -t "$DOCKER_IMAGE:$DOCKER_TAG" \
        -t "$DOCKER_REGISTRY/$DOCKER_IMAGE:$DOCKER_TAG" \
        .
    
    print_success "Docker image built successfully"
    docker images | grep "$DOCKER_IMAGE" | head -1
}

push_docker_image() {
    print_header "Pushing Docker Image to Registry"
    
    if [ "$DOCKER_REGISTRY" == "docker.io" ]; then
        print_warning "Ensure you are logged in to Docker Hub"
        echo "Run: docker login"
        read -p "Press enter to continue..."
    fi
    
    echo "Pushing: $DOCKER_REGISTRY/$DOCKER_IMAGE:$DOCKER_TAG"
    docker push "$DOCKER_REGISTRY/$DOCKER_IMAGE:$DOCKER_TAG"
    
    print_success "Docker image pushed successfully"
}

test_deployment() {
    print_header "Testing Deployment"
    
    if [ -z "$RUNPOD_ENDPOINT_ID" ]; then
        print_error "RUNPOD_ENDPOINT_ID environment variable not set"
        exit 1
    fi
    
    if [ -z "$RUNPOD_API_KEY" ]; then
        print_error "RUNPOD_API_KEY environment variable not set"
        exit 1
    fi
    
    print_warning "Testing RunPod endpoint: $RUNPOD_ENDPOINT_ID"
    
    # Test with a sample request
    TEST_PAYLOAD='{
        "input": {
            "test": true,
            "message": "Health check from deploy script"
        }
    }'
    
    echo "Sending test request to RunPod API..."
    RESPONSE=$(curl -s -X POST \
        "https://api.runpod.io/v2/$RUNPOD_ENDPOINT_ID/run" \
        -H "Authorization: Bearer $RUNPOD_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$TEST_PAYLOAD")
    
    echo "Response: $RESPONSE"
    
    if echo "$RESPONSE" | grep -q '"id"'; then
        JOB_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
        print_success "Test request submitted successfully (Job ID: $JOB_ID)"
        
        # Wait for result (with timeout)
        echo "Waiting for result (timeout: 30 seconds)..."
        TIMEOUT=30
        ELAPSED=0
        while [ $ELAPSED -lt $TIMEOUT ]; do
            STATUS_RESPONSE=$(curl -s -X GET \
                "https://api.runpod.io/v2/$RUNPOD_ENDPOINT_ID/status/$JOB_ID" \
                -H "Authorization: Bearer $RUNPOD_API_KEY")
            
            STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
            
            if [ "$STATUS" == "COMPLETED" ]; then
                print_success "Test completed successfully"
                echo "Result: $STATUS_RESPONSE"
                return 0
            elif [ "$STATUS" == "FAILED" ]; then
                print_error "Test failed"
                echo "Result: $STATUS_RESPONSE"
                return 1
            fi
            
            echo "Status: $STATUS (elapsed: ${ELAPSED}s)"
            sleep 2
            ELAPSED=$((ELAPSED + 2))
        done
        
        print_warning "Test timed out after $TIMEOUT seconds"
    else
        print_error "Failed to submit test request"
        echo "Response: $RESPONSE"
        exit 1
    fi
}

show_setup_instructions() {
    print_header "Setup Instructions"
    
    cat << 'EOF'

1. Create RunPod Serverless Endpoint
   - Visit: https://www.runpod.io/console/serverless
   - Click: Create New Template
   - Docker Image: <your-registry>/ivrimeet-runpod:latest
   - Endpoints: Select this template
   - Create Endpoint

2. Configure Environment Variables
   After endpoint creation, set these in RunPod endpoint settings:
   
   DATABASE_URL=postgresql://user:password@host:5432/ivrimeet_db
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   S3_BUCKET=your-bucket-name
   S3_REGION=us-east-1
   IVRIT_API_KEY=your_ivrit_key
   IVRIT_API_URL=https://api.ivrit.ai
   USE_RUNPOD=true

3. Get Your Credentials
   - Endpoint ID: Copy from RunPod console
   - API Key: Generate from RunPod API keys section

4. Configure Backend
   Export these environment variables before deploying backend:
   
   export RUNPOD_ENDPOINT_ID=ep-xxxxx
   export RUNPOD_API_KEY=your_api_key
   export USE_RUNPOD=true

5. Deploy Backend API
   Deploy to your preferred host (Render, Railway, etc.)

6. Test the Deployment
   ./scripts/deploy_runpod.sh --test

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD=true
            shift
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --create-endpoint)
            CREATE_ENDPOINT=true
            shift
            ;;
        --test)
            TEST=true
            shift
            ;;
        --all)
            BUILD=true
            PUSH=true
            TEST=true
            shift
            ;;
        --docker-registry)
            DOCKER_REGISTRY="$2"
            shift 2
            ;;
        --docker-image)
            DOCKER_IMAGE="$2"
            shift 2
            ;;
        --docker-tag)
            DOCKER_TAG="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
print_header "RunPod Serverless Deployment"

if [ "$BUILD" = false ] && [ "$PUSH" = false ] && [ "$TEST" = false ]; then
    print_warning "No action specified. Use --help for usage information"
    show_setup_instructions
    exit 0
fi

check_requirements

if [ "$BUILD" = true ]; then
    build_docker_image
fi

if [ "$PUSH" = true ]; then
    if [ "$BUILD" = false ]; then
        print_warning "Building image before pushing..."
        build_docker_image
    fi
    push_docker_image
fi

if [ "$CREATE_ENDPOINT" = true ]; then
    show_setup_instructions
fi

if [ "$TEST" = true ]; then
    test_deployment
fi

print_header "Deployment Complete"
echo "Next steps:"
echo "1. Ensure environment variables are configured"
echo "2. Deploy backend API"
echo "3. Test the deployment: ./scripts/deploy_runpod.sh --test"

