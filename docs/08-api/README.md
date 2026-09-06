# API

## REST

Контракт Order Service: [order-service.yaml](../../contracts/openapi/order-service.yaml).

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/api/v1/orders` | Создать заказ |
| GET | `/api/v1/orders/{orderId}` | Получить заказ |
| GET | `/health/live` | Проверить процесс API |
| GET | `/health/ready` | Проверить соединение с базой |

Swagger UI доступен по адресу `http://localhost:8000/docs` после запуска прототипа.

## События

Контракт событий: [order-events.yaml](../../contracts/asyncapi/order-events.yaml).

`order.created.v1` публикуется после создания заказа.

## Версии

Версия REST находится в пути.

Версия события находится в имени и поле `eventVersion`.

Добавление необязательного поля не меняет основную версию. Удаление поля, изменение типа или смысла требует новой основной версии.
