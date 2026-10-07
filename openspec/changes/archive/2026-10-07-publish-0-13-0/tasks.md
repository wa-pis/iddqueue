## 1. Candidate

- [x] 1.1 Обновить version/lock, README/install guides/changelog/release notes; проверить diff и сохранение RC истории.
- [x] 1.2 Выполнить полный release gate на выделенном PostgreSQL, build/LICENSE/installed profiles/async recipe; записать результаты и SHA256.
- [x] 1.3 Signed candidate push; подтвердить фактические Tests 6/6 и Documentation success на exact SHA.

## 2. Publication

- [x] 2.1 Signed tag и GitHub stable release exact assets; проверить tag/target и SHA256 downloaded assets.
- [x] 2.2 Pin publisher version/SHA/hashes, signed push; проверить remote workflow и OIDC PyPI success.
- [x] 2.3 Проверить PyPI metadata/hash, clean index installation/async recipe, actual publisher CI/docs; обновить evidence/roadmap и архивировать change.
