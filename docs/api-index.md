# Индекс HTTP контрактов

| Сервис | Метод и путь | Назначение |
|---|---|---|
| incident-service | `POST /api/v1/incidents` | Зарегистрировать происшествие |
| incident-service | `GET /api/v1/incidents` | Получить происшествия |
| incident-service | `GET /api/v1/incidents/{id}` | Прочитать происшествие |
| incident-service | `GET /internal/v1/incidents/{id}` | Получить снимок происшествия |
| resource-service | `POST /api/v1/teams` | Добавить бригаду с закреплённым комплектом техники |
| resource-service | `GET /api/v1/teams` | Получить бригады |
| resource-service | `GET /internal/v1/teams/{id}` | Проверить специализацию бригады |
| resource-service | `POST /internal/v1/reservations` | Атомарно зарезервировать бригаду |
| resource-service | `GET /internal/v1/reservations/{dispatchId}` | Уточнить результат резервирования |
| resource-service | `POST /internal/v1/reservations/{dispatchId}/confirm` | Подтвердить резерв |
| resource-service | `POST /internal/v1/reservations/{dispatchId}/release` | Освободить резерв |
| dispatch-service | `POST /api/v1/dispatches` | Начать назначение бригады |
| dispatch-service | `GET /api/v1/dispatches` | Получить назначения |
| dispatch-service | `GET /api/v1/dispatches/{id}` | Получить состояние саги |
| dispatch-service | `POST /api/v1/dispatches/{id}/cancel` | Запросить отмену назначения |
| operation-service | `PUT /internal/v1/operations/{dispatchId}` | Создать предложение работы бригаде |
| operation-service | `GET /internal/v1/operations/{dispatchId}` | Уточнить создание или завершение работы |
| operation-service | `POST /internal/v1/operations/{dispatchId}/cancel` | Отменить предложение до активации |
| operation-service | `GET /api/v1/operations` | Показать задания бригады |
| operation-service | `GET /api/v1/operations/{dispatchId}` | Прочитать задание |
| operation-service | `POST /api/v1/operations/{dispatchId}/decision` | Принять или отклонить предложение |
| operation-service | `POST /api/v1/operations/{dispatchId}/reports` | Зафиксировать прибытие или завершение |
| notification-service | `PUT /api/v1/notification-preferences` | Настроить собственные уведомления |
| notification-service | `GET /api/v1/notification-preferences` | Прочитать собственные настройки |
| notification-service | `GET /api/v1/notifications` | Получить историю своих уведомлений |
| notification-service | `POST /api/v1/notifications/{id}/retry` | Повторить неудавшуюся доставку |
