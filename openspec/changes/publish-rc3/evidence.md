# RC3 evidence

Local release gate выполнен на Python 3.13.14 / dedicated PostgreSQL 14.20 port 55433: полный unit/func suite, Ruff/uv lock/docs/strict MkDocs/OpenSpec/build/LICENSE/clean base and monitoring wheel acceptance/installed quickstart passed. Log /tmp/iddqueue-rc3-gate.log. Assets повторно собираются после candidate commit для фиксации точного SHA.

158 tests passed in 57.35s. Candidate 911ca1a3a197b1745af15f6a4bf399cd470ce969, signature verified; actual Tests 37536626612 success 6/6; Documentation 37536626558 success. Candidate wheel rebuilt and clean base/monitoring/quickstart rechecked successfully; initial extra acceptance invocation lacked IDDQUEUE_TEST_DATABASE guard, corrected to dedicated and rerun passed.
Signed tag v0.13.0rc3 и GitHub prerelease созданы. Wheel SHA256 25e56080f3871e9fa0553be67b3b21d4ace8b363abe42feab45f8f1363520bf9; sdist 3bcad9cc15030b3baedc40ef0bcf109d79d3a781f88a5f650f7d9129a540013a.
