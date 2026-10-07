## Context

Result publication предшествует ACK; прежняя delay проверка может оставить ACK, который следующий test ошибочно принимает. CI trace не позволяет отличить чужой ACK от завершения sleeper доSIGKILL. Поэтому исправить оба oracle gaps, без утверждения нового runtime crash defect.

## Decisions

crash_probe записывает started, ждёт ready marker с30sdeadline, store_results/max_retries0. Test ждёт started, SIGKILL group и reaps process, проверяет message-specific ResultTimeout, затем пишет ready marker; последующий restart_worker проверяет тотже message result. Existing session worker сохраняет crash_message для пары recovery tests. Listener.wait optional message_ids пропускает/дедуплицирует чужие ACK в пределах одного stream timeout. Существующие вызовы без filter остаются совместимы.

## Risks / Trade-offs

Пара crash/recover остаётся последовательной как ранее; marker сохраняется между ними. Не увеличивать duration sleeper как исправление. DedicatedPG обязательна.
