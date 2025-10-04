#!/bin/bash

# Lambda Deployment Script for AIVE Video Renderer
# Usage: ./deploy.sh [stage] [method]
# Example: ./deploy.sh dev serverless
# Example: ./deploy.sh prod docker

set -e

STAGE=${1:-dev}
METHOD=${2:-serverless}

echo "======================================"
echo "AIVE Video Renderer Deployment"
echo "======================================"
echo "Stage: $STAGE"
echo "Method: $METHOD"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required tools are installed
check_dependencies() {
    echo "Checking dependencies..."
    
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}Error: AWS CLI is not installed${NC}"
        echo "Install it from: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    if [ "$METHOD" = "serverless" ]; then
        if ! command -v serverless &> /dev/null; then
            echo -e "${RED}Error: Serverless Framework is not installed${NC}"
            echo "Install it with: npm install -g serverless"
            exit 1
        fi
    fi
    
    if [ "$METHOD" = "docker" ]; then
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}Error: Docker is not installed${NC}"
            echo "Install it from: https://www.docker.com/"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✓ All dependencies installed${NC}"
    echo ""
}

# Deploy using Serverless Framework
deploy_serverless() {
    echo "Deploying with Serverless Framework..."
    
    # Install npm packages if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing npm packages..."
        npm install
    fi
    
    # Deploy
    echo "Deploying to stage: $STAGE"
    serverless deploy --stage $STAGE
    
    echo ""
    echo -e "${GREEN}✓ Deployment complete!${NC}"
    echo ""
    echo "Getting function info..."
    serverless info --stage $STAGE
}

# Deploy using Docker
deploy_docker() {
    echo "Deploying with Docker..."
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=${AWS_REGION:-us-east-1}
    ECR_REPO="aive-video-renderer"
    IMAGE_TAG="${STAGE}-$(date +%Y%m%d-%H%M%S)"
    
    echo "AWS Account: $AWS_ACCOUNT_ID"
    echo "AWS Region: $AWS_REGION"
    echo "ECR Repository: $ECR_REPO"
    echo "Image Tag: $IMAGE_TAG"
    echo ""
    
    # Create ECR repository if it doesn't exist
    echo "Checking ECR repository..."
    if ! aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION &> /dev/null; then
        echo "Creating ECR repository..."
        aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION
    else
        echo -e "${GREEN}✓ ECR repository exists${NC}"
    fi
    echo ""
    
    # Build Docker image
    echo "Building Docker image..."
    docker build -t $ECR_REPO:$IMAGE_TAG .
    docker tag $ECR_REPO:$IMAGE_TAG $ECR_REPO:latest
    echo -e "${GREEN}✓ Docker image built${NC}"
    echo ""
    
    # Login to ECR
    echo "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
    echo ""
    
    # Tag and push to ECR
    echo "Tagging and pushing image to ECR..."
    docker tag $ECR_REPO:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG
    docker tag $ECR_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
    
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
    echo -e "${GREEN}✓ Image pushed to ECR${NC}"
    echo ""
    
    # Get Lambda function name
    FUNCTION_NAME="aive-video-renderer-$STAGE"
    
    # Check if Lambda function exists
    if aws lambda get-function --function-name $FUNCTION_NAME --region $AWS_REGION &> /dev/null; then
        echo "Updating existing Lambda function..."
        aws lambda update-function-code \
            --function-name $FUNCTION_NAME \
            --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG \
            --region $AWS_REGION
        echo -e "${GREEN}✓ Lambda function updated${NC}"
    else
        echo -e "${YELLOW}Warning: Lambda function '$FUNCTION_NAME' not found${NC}"
        echo "Please create it manually in AWS Console or use Serverless Framework"
        echo "ECR Image URI: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"
    fi
    
    echo ""
    echo -e "${GREEN}✓ Docker deployment complete!${NC}"
}

# Main execution
check_dependencies

case $METHOD in
    serverless)
        deploy_serverless
        ;;
    docker)
        deploy_docker
        ;;
    *)
        echo -e "${RED}Error: Unknown deployment method '$METHOD'${NC}"
        echo "Supported methods: serverless, docker"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "Next Steps:"
echo "======================================"
echo "1. Update your backend .env file:"
echo "   USE_LAMBDA_RENDERING=true"
echo "   LAMBDA_FUNCTION_NAME=aive-video-renderer-$STAGE-renderVideo"
echo "   S3_BUCKET=aive-rendered-videos"
echo ""
echo "2. Test the Lambda function:"
if [ "$METHOD" = "serverless" ]; then
    echo "   serverless invoke -f renderVideo --stage $STAGE --data '{...}'"
fi
echo ""
echo "3. Monitor logs:"
if [ "$METHOD" = "serverless" ]; then
    echo "   serverless logs -f renderVideo --stage $STAGE --tail"
fi
echo "   Or use CloudWatch Logs in AWS Console"
echo "======================================"
