## 1. Release

- [x] 1.1 Проверить PUBLIC visibility и отсутствие конфликтующего tag/release; сверить локальные SHA256 с candidate evidence.
- [x] 1.2 Создать GitHub prerelease v0.13.0rc1 на candidate SHA, загрузить wheel/sdist/SHA256SUMS; проверить isPrerelease, targetCommitish и remote asset digests.
- [x] 1.2a Добавить и проверить publish.yml, environment pypi, main-only manual trigger и fixed asset hashes; commit/push и actual CI.
- [x] 1.3 Настроить безопасную PyPI authentication и опубликовать точные artifacts; проверить PyPI version metadata/hashes и чистую index installation.
- [ ] 1.4 Обновить publication docs/evidence, архивировать change после обеих публикаций; strict OpenSpec и commit/push.
