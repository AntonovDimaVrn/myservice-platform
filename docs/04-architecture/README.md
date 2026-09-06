# Архитектура

## Подход

Целевая система проектируется как набор сервисов по бизнес-областям. Разделение по типам услуг не используется. Химчистка, клининг, дезинсекция и дезинфекция являются записями каталога.

На текущем этапе работает только Order Service. Остальные компоненты являются проектным решением.

## Компоненты

| Компонент | Ответственность | Статус |
|---|---|---|
| Client PWA | Каталог, расчёт и заказ | План |
| Master PWA | Расписание и выполнение работ | План |
| Admin UI | Заказы, услуги, пользователи и статистика | План |
| API Gateway | Единая точка входа | План |
| Keycloak | Вход, роли и 2FA | План |
| Catalog Service | Услуги и правила цены | План |
| Order Service | Заказ и его жизненный цикл | Прототип |
| Scheduling Service | Слоты, мастера и назначения | План |
| Notification Service | SMS, email и push | План |
| Payment Service | Оплата и возвраты | План |
| Analytics Service | Отчёты и показатели | План |
| RabbitMQ | Асинхронные события | Прототип |

## Принципы

Каждый сервис владеет своими данными.

REST используется, когда пользователю нужен немедленный ответ.

RabbitMQ используется для фоновой реакции на изменения.

События не содержат персональные данные клиента.

Изменение заказа и создание события выполняются в одной транзакции через outbox.

## Схемы

| Схема | Исходник | Просмотр |
|---|---|---|
| C4 Context | [system-context.puml](diagrams/system-context.puml) | [SVG](diagrams/system-context.svg) |
| C4 Container | [containers.puml](diagrams/containers.puml) | [SVG](diagrams/containers.svg) |
| UML Use Case | [use-cases.puml](diagrams/use-cases.puml) | [SVG](diagrams/use-cases.svg) |
| UML Sequence | [create-order-sequence.puml](diagrams/create-order-sequence.puml) | [SVG](diagrams/create-order-sequence.svg) |
| UML State | [order-state.puml](diagrams/order-state.puml) | [SVG](diagrams/order-state.svg) |
| RabbitMQ | [rabbitmq-flow.puml](diagrams/rabbitmq-flow.puml) | [SVG](diagrams/rabbitmq-flow.svg) |

## Поток создания заказа

1. Клиент отправляет данные заказа.
2. Order API проверяет запрос.
3. Order API сохраняет заказ и outbox-событие в одной транзакции.
4. Клиент получает идентификатор и статус `new`.
5. Worker читает неопубликованное событие.
6. Worker отправляет `order.created.v1` в RabbitMQ.
7. После подтверждения брокера worker отмечает событие опубликованным.

## Развёртывание прототипа

Прототип запускается в Docker Compose. Он содержит API, worker, PostgreSQL и RabbitMQ. Внешний балансировщик, Keycloak и мониторинг пока не запускаются.
