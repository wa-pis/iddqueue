# RC3 evidence

Local release gate выполнен на Python 3.13.14 / dedicated PostgreSQL 14.20 port 55433: полный unit/func suite, Ruff/uv lock/docs/strict MkDocs/OpenSpec/build/LICENSE/clean base and monitoring wheel acceptance/installed quickstart passed. Log /tmp/iddqueue-rc3-gate.log. Assets повторно собираются после candidate commit для фиксации точного SHA.

158 tests passed in 57.35s. Candidate 911ca1a3a197b1745af15f6a4bf399cd470ce969, signature verified; actual Tests 37536626612 success 6/6; Documentation 37536626558 success. Candidate wheel rebuilt and clean base/monitoring/quickstart rechecked successfully; initial extra acceptance invocation lacked IDDQUEUE_TEST_DATABASE guard, corrected to dedicated and rerun passed.
Signed tag v0.13.0rc3 и GitHub prerelease созданы. Wheel SHA256 25e56080f3871e9fa0553be67b3b21d4ace8b363abe42feab45f8f1363520bf9; sdist 3bcad9cc15030b3baedc40ef0bcf109d79d3a781f88a5f650f7d9129a540013a.

## Публикация и завершение — 2026-10-07

GitHub remote assets downloaded /tmp/iddqueue-rc3-remote, SHA256SUMS verified; prerelease target точный candidate SHA. OIDC workflow commit e443dd8bac9ad3f92032ccaadcb6fe99190a85d5; publication https://github.com/wa-pis/iddqueue/actions/runs/37537043153 success. Дополнительный tag Tests 37536985382 success, publish-workflow commit Tests 37537042376 6/6 success и Documentation 37537042321 success.
PyPI https://pypi.org/project/iddqueue/0.13.0rc3/ JSON file hashes совпадают с GitHub candidate wheel/sdist. Clean index environment /tmp/iddqueue-rc3-index: exact 0.13.0rc3 install, Domain routing/name/prebinding guard verified, installed quickstart six tables/result=5/cleanup passed. Первая установка увидела ещё старый index; refresh затем выявил пропавший файл локального uv cache; --no-cache retry прошёл.
Все четыре release tasks выполнены; release-only change skip_specs, runtime specs уже актуальны. Архив 2026-10-07; RC1/RC2 не изменены.
