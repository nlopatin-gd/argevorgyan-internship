#!/bin/bash
set -e
AWS_REGION="eu-north-1"
AWS_ACCOUNT_ID="113304117666"
IMAGE_NAME="nodejstask-ar"
IMAGE_TAG="latest"

aws ecr get-login-password --region $AWS_REGION | \
docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -t $IMAGE_NAME:$IMAGE_TAG .

docker tag $IMAGE_NAME:$IMAGE_TAG \
$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_TAG

docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_TAG
