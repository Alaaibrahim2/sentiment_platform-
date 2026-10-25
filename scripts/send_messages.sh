
#!/usr/bin/env bash

PRODUCER_URL="http://localhost:8000/predict"

messages=(
  "I absolutely love this product!"
  "This service is terrible and disappointing."
  "The food was delicious and the staff were wonderful."
  "I hate this application. It is slow and useless."
  "Today is a beautiful day and I feel amazing."
  "The experience was awful. I will never return."
  "The movie was fantastic and I really enjoyed it."
  "The customer support was rude and unhelpful."
  "I am very happy with the results."
  "This is the worst purchase I have ever made."
  "The application works perfectly!"
  "I am extremely disappointed with this service."
)

for i in "${!messages[@]}"; do
  message="${messages[$i]}"

  echo "[$((i + 1))/${#messages[@]}] Sending: $message"

  curl -sS --fail-with-body \
    -X POST "$PRODUCER_URL" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg text "$message" '{text: $text}')"

  echo
  echo "----------------------------------------"

  sleep 0.2
done

echo "Finished sending messages."

