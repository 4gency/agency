# Variables
$DOCKERHUB_USERNAME = "nitruusz"
$IMAGE_NAME = "botmock"
$TAG = "latest"
$DOCKERFILE_PATH = "."

# Function to check the last exit code
function Check-LastExitCode {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error in previous command. Stopping script." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# Log start
Write-Host "Starting Docker Hub build, tag, and push process" -ForegroundColor Cyan

# Step 1: Build Image
Write-Host "Building Docker image..." -ForegroundColor Green
docker build -t "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${TAG}" $DOCKERFILE_PATH
Check-LastExitCode

# Step 2: Tag Image
Write-Host "Tagging image..." -ForegroundColor Green
docker tag "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${TAG}" "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${TAG}"
Check-LastExitCode

# Step 3: Push Image
Write-Host "Pushing image to Docker Hub..." -ForegroundColor Green
docker push "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${TAG}"
Check-LastExitCode

# Log completion
Write-Host "Process completed successfully!" -ForegroundColor Green
