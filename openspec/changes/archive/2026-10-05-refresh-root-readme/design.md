## Context

README содержит более 700 строк, detailed recipes начиная с Transactional publishing. Existing docs/user-guide.rst ссылки ведут в README. Published PyPI 0.13.0rc1 и tested Python/PG matrix проверены ранее.

## Goals / Non-Goals

**Goals:** короткое первое знакомство, runnable minimal actor/start/send/result, подробные recipes доступны отдельно.

**Non-Goals:** runtime изменение, удаление recipes/credits, новая публикация или новая performance guarantee.

## Decisions

Сохранить comparison section anchor в README. Detailed section перенести без изменения API/примеров в docs/recipes.md, исправить relative license link и связанные ссылки из user guide/API. Quickstart использует отдельный worker и producer, global/explicit broker, Results и finally close owned producer pool. Проверить пример на dedicated PostgreSQL, docs links и build/LICENSE (README попадает в metadata), actual CI.

## Risks / Trade-offs

External deep links на старые README recipes могут сменить место → README содержит ссылку на рецепты, internal links обновлены. PyPI rendered README immutable RC остаётся старым до следующего release.
