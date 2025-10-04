# Use AWS Lambda Python base image for ARM64
FROM public.ecr.aws/lambda/python:3.11-arm64

# Install system dependencies
RUN yum update -y && \
    yum install -y \
    tar \
    xz \
    wget \
    libsndfile \
    && yum clean all

# Download and install static FFmpeg binary for ARM64
RUN cd /tmp && \
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz && \
    tar xf ffmpeg-release-arm64-static.tar.xz && \
    cd ffmpeg-*-arm64-static && \
    cp ffmpeg ffprobe /usr/local/bin/ && \
    cd / && \
    rm -rf /tmp/ffmpeg-*

# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "handler.lambda_handler" ]
