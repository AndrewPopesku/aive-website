# AWS Lambda Video Renderer

This Lambda function handles video rendering for the AIVE project. It's designed to offload the compute-intensive video processing from the FastAPI backend to AWS Lambda, which can handle longer processing times and more resources.

## Architecture

The video rendering process works as follows:
1. FastAPI backend receives a render request
2. Backend invokes Lambda function with project data and URLs
3. Lambda downloads footage, audio, and music files
4. Lambda renders the video using MoviePy
5. Lambda uploads the rendered video to S3
6. Lambda returns the S3 URL to the backend
7. Backend updates the project with the video URL

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured (`aws configure`)
- Docker installed (for container deployment)
- Serverless Framework installed: `npm install -g serverless`
- Serverless plugins:
  ```bash
  npm install --save-dev serverless-python-requirements serverless-offline
  ```

## Configuration

### Environment Variables

Set the following environment variables in your `.env` file or AWS Console:

**Lambda Environment:**
- `S3_BUCKET`: S3 bucket name for storing rendered videos (default: `aive-rendered-videos`)
- `ENVIRONMENT`: Environment name (dev, staging, prod)

**Backend Environment:**
- `AWS_REGION`: AWS region (default: `us-east-1`)
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `LAMBDA_FUNCTION_NAME`: Lambda function name (e.g., `aive-video-renderer-dev-renderVideo`)
- `S3_BUCKET`: S3 bucket name for videos
- `USE_LAMBDA_RENDERING`: Set to `true` to enable Lambda rendering

## Deployment Options

### Option 1: Using Serverless Framework (Recommended)

1. **Install dependencies:**
   ```bash
   cd lambda
   npm install
   ```

2. **Configure AWS credentials:**
   ```bash
   aws configure
   # Or use environment variables
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   ```

3. **Deploy to AWS:**
   ```bash
   # Deploy to dev stage
   serverless deploy --stage dev
   
   # Deploy to production
   serverless deploy --stage prod
   ```

4. **Get the function details:**
   ```bash
   serverless info --stage dev
   ```
   Note the function name and API endpoint.

### Option 2: Manual Docker Container Deployment

1. **Build the Docker image:**
   ```bash
   cd lambda
   docker build -t aive-video-renderer .
   ```

2. **Create ECR repository:**
   ```bash
   aws ecr create-repository --repository-name aive-video-renderer --region us-east-1
   ```

3. **Tag and push to ECR:**
   ```bash
   # Get ECR login
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Tag image
   docker tag aive-video-renderer:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/aive-video-renderer:latest
   
   # Push image
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/aive-video-renderer:latest
   ```

4. **Create Lambda function from container:**
   - Go to AWS Lambda Console
   - Create function → Container image
   - Browse images → Select your ECR image
   - Configure:
     - Memory: 10240 MB (10 GB)
     - Timeout: 900 seconds (15 minutes)
     - Ephemeral storage: 10240 MB
     - Environment variables: `S3_BUCKET`, etc.

## Configuration Details

### Lambda Settings

- **Memory:** 10 GB (maximum) - needed for video processing
- **Timeout:** 15 minutes (maximum) - video rendering can take time
- **Ephemeral Storage:** 10 GB - for temporary video files
- **Runtime:** Python 3.11
- **Architecture:** x86_64

### IAM Permissions

The Lambda function needs the following permissions:
- `s3:PutObject` - Upload rendered videos
- `s3:PutObjectAcl` - Set object permissions
- `s3:GetObject` - Read files if needed
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` - CloudWatch logging

## Testing

### Test Locally with Docker

```bash
cd lambda
docker build -t aive-video-renderer .
docker run -p 9000:8080 -e S3_BUCKET=test-bucket aive-video-renderer

# In another terminal, invoke the function
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d @test_event.json
```

### Create a test event (`test_event.json`):

```json
{
  "body": "{\"project_data\": {\"id\": \"test-project\", \"sentences\": []}, \"audio_url\": \"https://example.com/audio.mp3\", \"music_url\": null}"
}
```

### Test on AWS

```bash
serverless invoke -f renderVideo --data '{"body": "{\"project_data\": {...}, \"audio_url\": \"...\"}"}' --stage dev
```

## Monitoring

### CloudWatch Logs

Lambda execution logs are automatically sent to CloudWatch:
```bash
# View logs
serverless logs -f renderVideo --stage dev --tail

# Or use AWS CLI
aws logs tail /aws/lambda/aive-video-renderer-dev-renderVideo --follow
```

### Metrics to Monitor

- **Duration:** How long each render takes
- **Memory Usage:** Ensure it doesn't exceed limits
- **Errors:** Track failed renders
- **Throttles:** Check if you're hitting concurrency limits

## Cost Optimization

1. **Use Reserved Concurrency:** Limit concurrent executions if needed
2. **Monitor Execution Time:** Optimize video processing to reduce duration
3. **Use Appropriate Memory:** 10 GB is max, but test if less works
4. **S3 Lifecycle Policies:** Archive or delete old videos automatically

## Troubleshooting

### Common Issues

1. **Timeout Errors:**
   - Check video complexity and duration
   - Increase timeout (max 15 minutes)
   - Consider splitting large videos

2. **Out of Memory:**
   - Already at max (10 GB)
   - Optimize video processing
   - Consider using EC2 for very large videos

3. **S3 Upload Fails:**
   - Check IAM permissions
   - Verify bucket exists and is accessible
   - Check bucket region matches Lambda region

4. **MoviePy Errors:**
   - Ensure FFmpeg is installed in container
   - Check video format compatibility
   - Verify font availability for subtitles

## Backend Integration

Update your backend `.env` file:

```env
USE_LAMBDA_RENDERING=true
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
LAMBDA_FUNCTION_NAME=aive-video-renderer-dev-renderVideo
S3_BUCKET=aive-rendered-videos
```

## Rollback

If you need to rollback to local rendering:

1. Set `USE_LAMBDA_RENDERING=false` in backend `.env`
2. Restart backend service
3. Old local rendering will be used

## Cleanup

To remove the Lambda function and resources:

```bash
serverless remove --stage dev
```

Or manually delete:
- Lambda function
- S3 bucket (and contents)
- CloudWatch log groups
- ECR repository (if used)

## Future Improvements

1. **Async Processing:** Use SQS for async video rendering queue
2. **Progress Updates:** Implement progress callbacks to backend
3. **Video Chunking:** Split large videos for parallel processing
4. **Caching:** Cache frequently used footage/music
5. **Auto-scaling:** Use Step Functions for complex workflows
