gcloud run deploy shorts-bot --source . --region us-central1 \
  --cpu 1 --memory 512Mi --min-instances 1 --max-instances 1 \
  --no-allow-unauthenticated
