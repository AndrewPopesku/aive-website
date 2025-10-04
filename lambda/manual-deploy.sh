#!/bin/bash

# Manual Lambda Deployment Script
# This script builds and deploys the Lambda function manually without Serverless Framework

set -e

# Configuration
REGION="eu-west-1"
FUNCTION_NAME="aive-video-renderer-dev"
ECR_REPO_NAME="aive-video-renderer"
ROLE_NAME="aive-video-renderer-role"
S3_BUCKET="aive-video-render-dev"

echo "========================================"
echo "Manual Lambda Deployment"
echo "========================================"
echo ""

# Get AWS Account ID
echo "Getting AWS account information..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO_NAME}"

echo "AWS Account ID: ${AWS_ACCOUNT_ID}"
echo "Region: ${REGION}"
echo "ECR Repository: ${ECR_URI}"
echo ""

# Step 1: Create ECR Repository
echo "Step 1: Creating ECR repository..."
if aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} --region ${REGION} 2>/dev/null; then
    echo "✓ ECR repository already exists"
else
    echo "Creating ECR repository..."
    aws ecr create-repository \
        --repository-name ${ECR_REPO_NAME} \
        --region ${REGION} \
        --image-scanning-configuration scanOnPush=true
    echo "✓ ECR repository created"
fi
echo ""

# Step 2: Build Docker image
echo "Step 2: Building Docker image..."
echo "Using legacy Docker builder (not buildx) to ensure compatible manifest format..."
DOCKER_BUILDKIT=0 docker build --no-cache -t ${ECR_REPO_NAME}:latest .
echo "✓ Docker image built"
echo ""

# Step 3: Tag image for ECR
echo "Step 3: Tagging image..."
docker tag ${ECR_REPO_NAME}:latest ${ECR_URI}:latest
docker tag ${ECR_REPO_NAME}:latest ${ECR_URI}:$(date +%Y%m%d-%H%M%S)
echo "✓ Image tagged"
echo ""

# Step 4: Login to ECR
echo "Step 4: Logging into ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_URI}
echo "✓ Logged into ECR"
echo ""

# Step 5: Push image to ECR
echo "Step 5: Pushing image to ECR..."
docker push ${ECR_URI}:latest
echo "✓ Image pushed to ECR"
echo ""

# Step 6: Create IAM role for Lambda (if doesn't exist)
echo "Step 6: Setting up IAM role..."
if aws iam get-role --role-name ${ROLE_NAME} 2>/dev/null; then
    echo "✓ IAM role already exists"
    ROLE_ARN=$(aws iam get-role --role-name ${ROLE_NAME} --query 'Role.Arn' --output text)
else
    echo "Creating IAM role..."
    
    # Create trust policy
    cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
    
    # Create role
    ROLE_ARN=$(aws iam create-role \
        --role-name ${ROLE_NAME} \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --query 'Role.Arn' \
        --output text)
    
    # Attach basic Lambda execution policy
    aws iam attach-role-policy \
        --role-name ${ROLE_NAME} \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    # Create and attach S3 access policy
    cat > /tmp/s3-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::${S3_BUCKET}/*"
    }
  ]
}
EOF
    
    aws iam put-role-policy \
        --role-name ${ROLE_NAME} \
        --policy-name s3-access \
        --policy-document file:///tmp/s3-policy.json
    
    echo "✓ IAM role created: ${ROLE_ARN}"
    echo "Waiting 10 seconds for IAM role to propagate..."
    sleep 10
fi
echo ""

# Step 7: Create S3 bucket (if doesn't exist)
echo "Step 7: Creating S3 bucket..."
if aws s3 ls "s3://${S3_BUCKET}" 2>/dev/null; then
    echo "✓ S3 bucket already exists"
else
    echo "Creating S3 bucket..."
    if [ "${REGION}" = "us-east-1" ]; then
        aws s3 mb "s3://${S3_BUCKET}"
    else
        aws s3 mb "s3://${S3_BUCKET}" --region ${REGION}
    fi
    
    # Configure CORS
    cat > /tmp/cors.json <<EOF
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedOrigins": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}
EOF
    
    aws s3api put-bucket-cors \
        --bucket ${S3_BUCKET} \
        --cors-configuration file:///tmp/cors.json
    
    echo "✓ S3 bucket created"
fi
echo ""

# Step 8: Create or update Lambda function
echo "Step 8: Creating/updating Lambda function..."
if aws lambda get-function --function-name ${FUNCTION_NAME} --region ${REGION} 2>/dev/null; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name ${FUNCTION_NAME} \
        --image-uri ${ECR_URI}:latest \
        --region ${REGION}
    
    echo "Waiting for function update to complete..."
    aws lambda wait function-updated --function-name ${FUNCTION_NAME} --region ${REGION}
    
    echo "Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name ${FUNCTION_NAME} \
        --memory-size 3008 \
        --timeout 900 \
        --ephemeral-storage Size=10240 \
        --environment "Variables={S3_BUCKET=${S3_BUCKET},ENVIRONMENT=dev}" \
        --region ${REGION}
    
    echo "✓ Lambda function updated"
else
    echo "Creating new Lambda function..."
    aws lambda create-function \
        --function-name ${FUNCTION_NAME} \
        --package-type Image \
        --code ImageUri=${ECR_URI}:latest \
        --role ${ROLE_ARN} \
        --memory-size 3008 \
        --timeout 900 \
        --ephemeral-storage Size=10240 \
        --architectures arm64 \
        --environment "Variables={S3_BUCKET=${S3_BUCKET},ENVIRONMENT=dev}" \
        --region ${REGION}
    
    echo "✓ Lambda function created"
fi
echo ""

# Step 9: Create Function URL (optional - for HTTP access)
echo "Step 9: Creating Function URL..."
if aws lambda get-function-url-config --function-name ${FUNCTION_NAME} --region ${REGION} 2>/dev/null; then
    echo "✓ Function URL already exists"
    FUNCTION_URL=$(aws lambda get-function-url-config --function-name ${FUNCTION_NAME} --region ${REGION} --query 'FunctionUrl' --output text)
else
    echo "Creating Function URL..."
    FUNCTION_URL=$(aws lambda create-function-url-config \
        --function-name ${FUNCTION_NAME} \
        --auth-type NONE \
        --region ${REGION} \
        --query 'FunctionUrl' \
        --output text)
    
    # Add permission for public access
    aws lambda add-permission \
        --function-name ${FUNCTION_NAME} \
        --statement-id FunctionURLAllowPublicAccess \
        --action lambda:InvokeFunctionUrl \
        --principal "*" \
        --function-url-auth-type NONE \
        --region ${REGION} 2>/dev/null || echo "Permission already exists"
    
    echo "✓ Function URL created"
fi
echo ""

# Cleanup temp files
rm -f /tmp/trust-policy.json /tmp/s3-policy.json /tmp/cors.json

echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo ""
echo "Function Name: ${FUNCTION_NAME}"
echo "Function URL:  ${FUNCTION_URL}"
echo "ECR Image:     ${ECR_URI}:latest"
echo "S3 Bucket:     ${S3_BUCKET}"
echo ""
echo "Test the function with:"
echo "aws lambda invoke --function-name ${FUNCTION_NAME} --region ${REGION} --payload '{\"body\":\"{}\"}' response.json"
echo ""
echo "View logs with:"
echo "aws logs tail /aws/lambda/${FUNCTION_NAME} --region ${REGION} --follow"
