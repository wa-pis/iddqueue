## Decisions

Переиспользовать Dramatiq Actor, не proxy и не собственный task runner. Private declaration Broker не имеет middleware и отклоняет enqueue. Domain.actor строит Actor напрямую: queue валидируется при Domain construction, middleware options проверяются при register на реальном broker. Имена domain.function, explicit actor_name тоже квалифицируется. queue_name/broker overrides не допускаются.

Все options/name collisions проверяются до registration. Повторная register с тем же broker no-op; с другим broker ошибка. Actors нельзя добавлять после register. Регистрация до worker threads startup, без hot rebind/unregister; для независимых app/test instances нужны новые Domain instances. Pool ownership остаётся у caller. На hook exception все actor handles возвращаются к declaration broker (enqueue снова запрещён). Registration hook exceptions могут оставить частичное состояние реального broker,  как штатная Dramatiq registration; broker/domain в таком случае не переиспользовать.

Explicit app worker создаёт broker из DSN при startup, устанавливает global broker для CLI/composition, регистрирует выбранные domains. Стандартные Actor send/message/options/callbacks/async адаптация остаются native. До register прямой вызов и message construction разрешены, enqueue запрещён. Domain queue routing не security isolation. Один broker на worker CLI; several DSN не обещаются.

Docker image application example с exec CMD и external runtime DSN; actual container запуск возможен только при доступном engine. Проверить отдельный spawned Dramatiq worker независимо от FastAPI.
