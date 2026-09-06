#!/usr/bin/env bash

set -euo pipefail

api_url="${API_URL:-http://localhost:8000}"

create_response="$({
  curl --fail --silent --show-error \
    --request POST \
    --header "Content-Type: application/json" \
    --data '{
      "serviceType": "dry_cleaning",
      "customerName": "Тестовый клиент",
      "customerPhone": "+79990000000",
      "address": "Москва, тестовый адрес, дом 1",
      "desiredAt": "2099-01-01T10:00:00+00:00",
      "comment": "Проверка локального запуска"
    }' \
    "${api_url}/api/v1/orders"
})"

order_id="$(printf '%s' "${create_response}" | python3 -c 'import json, sys; print(json.load(sys.stdin)["id"])')"

curl --fail --silent --show-error "${api_url}/api/v1/orders/${order_id}" >/dev/null

published="0"
for _ in $(seq 1 20); do
  published="$(docker compose exec -T postgres psql \
    --username "${POSTGRES_USER:-myservice}" \
    --dbname "${POSTGRES_DB:-myservice}" \
    --tuples-only \
    --no-align \
    --command "SELECT count(*) FROM outbox_events WHERE aggregate_id = '${order_id}' AND published_at IS NOT NULL;")"
  if [ "${published}" = "1" ]; then
    break
  fi
  sleep 1
done

if [ "${published}" != "1" ]; then
  echo "Outbox event was not published" >&2
  exit 1
fi

echo "Smoke test passed for order ${order_id}"
