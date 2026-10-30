# Контракты событий

Все события публикуются в durable topic exchange `city.events`. У каждого подписчика своя durable очередь `<service>.events`, привязанная к перечисленным routing keys. Сообщения persistent, доставка at-least-once. Схемы находятся в OpenAPI издателя.

| Routing key | Издатель | Подписчики | Схема |
|---|---|---|---|
| `incident.created` | incident-service | dispatch-service | [IncidentCreated](../api/incident-service.yaml#/components/schemas/IncidentCreated) |
| `operation.accepted` | operation-service | dispatch-service | [OperationAccepted](../api/operation-service.yaml#/components/schemas/OperationAccepted) |
| `operation.rejected` | operation-service | dispatch-service | [OperationRejected](../api/operation-service.yaml#/components/schemas/OperationRejected) |
| `operation.completed` | operation-service | dispatch-service | [OperationCompleted](../api/operation-service.yaml#/components/schemas/OperationCompleted) |
| `dispatch.confirmed` | dispatch-service | operation-service, notification-service | [DispatchConfirmed](../api/dispatch-service.yaml#/components/schemas/DispatchConfirmed) |
| `dispatch.cancelled` | dispatch-service | notification-service | [DispatchCancelled](../api/dispatch-service.yaml#/components/schemas/DispatchCancelled) |
| `dispatch.completed` | dispatch-service | incident-service, notification-service | [DispatchCompleted](../api/dispatch-service.yaml#/components/schemas/DispatchCompleted) |

`eventId` — идентификатор конкретного события, `correlationId` — UUID саги (для incident.created — UUID происшествия), `aggregateVersion` — монотонная версия агрегата издателя; версии разных издателей не сравниваются. Все времена UTC.

dispatch-service использует incident.created для локального списка новых обращений; автоматического резервирования событие не запускает. operation.accepted/rejected меняют состояние саги только из ожидаемого состояния. dispatch.confirmed активирует ACCEPTED → ACTIVE. operation.completed инициирует освобождение ресурса, после чего dispatch.completed закрывает происшествие. Уведомления о подтверждении, отмене и завершении адресованы recipientUserId.

После пяти неуспешных обработок (1, 5, 30, 120, 600 секунд) сообщение переносится в `<service>.dlq`; оператор устраняет причину и повторно публикует его с прежним eventId. Неизвестная schemaVersion → DLQ. Корреляция не заменяет дедупликацию: уникальный inbox(eventId) записывается вместе с изменением состояния. При нарушении порядка переходы проверяются; пропуск версии записывается в диагностику, события не применяются слепо.
