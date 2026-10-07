# RC5 evidence — 2026-10-07

## Scope

Пользователь авторизовал GitHub/PyPI RC5; async feature signed dc6539b, static diff scan e0ffea74-d1ef-47b0-977b-a93c6a43bcbe complete/findings0 для e56c6b1..414e1c6. Scope20changed paths, не dependency CVE/production grants audit. NoDDLfromRC4, historical RC assets сохранены.

## Local gate

Python3.13.14/PostgreSQL14.20 выделенный cluster /tmp/iddqueue-domains-pg, port55433, IDDQUEUE_TEST_DATABASE=dedicated.
`PGHOST=127.0.0.1 PGPORT=55433 PGUSER=postgres PGDATABASE=postgres IDDQUEUE_TEST_DATABASE=dedicated PATH=/tmp/iddqueue-docsite-env/bin:/opt/homebrew/bin:$PATH UV_PROJECT_ENVIRONMENT=/tmp/iddqueue-docsite-env UV_CACHE_DIR=/tmp/iddqueue-uv-cache PYTHON=/tmp/iddqueue-docsite-env/bin/python UV=/opt/homebrew/bin/uv sh scripts/check_release.sh`: exit0, **200passed55.84s**. Full locked sync/pipcheck/Ruff, async business transaction actor result/cleanup, strictdocs/check_docs, OpenSpec20/20, build/LICENSE, isolated installedbase/monitoring/SQLAlchemy profiles and quickstartresult5 allpassed. Log /tmp/iddqueue-rc5-gate.log.

Initial uv lock network in sandbox failed; offline cached lock rerun passed, only iddqueue version changed. No dependency upgrades. Publisher workflow still RC4 until RC5 candidate/hash is verified.

GitHub About updated and actual API readback matched: PostgreSQL broker and Results backend for Dramatiq with Psycopg 3. Durable queues, sync/async transactional publishing, domain actors and monitoring. Homepage unchanged.

## Immutable assets

b80dc688df636f63c380cbb6a287417260fbd926239ea2d6826621585c22ec36  iddqueue-0.13.0rc5-py3-none-any.whl
5ed7cbb9a164aef0581b473d9c8fa5b23a7ca171f49287039aae15e7e57a63bc  iddqueue-0.13.0rc5.tar.gz

## Remote

Candidate CI, publication and readbacks completed; results below.

## Candidate and GitHub publication

Signedcandidate186542bdf615ea48cb53a8142cc588f5726af5f8 pushedmain; GitHubverified=true/reasonvalid. Tests37587847172success/all6jobsfirstattempt; Documentation37587847095success. Signedtagv0.13.0rc5 verified and pushed; GitHub https://github.com/wa-pis/iddqueue/releases/tag/v0.13.0rc5 isPrerelease=true, targetCommitish exactcandidate. Wheel36744bytes/sdist27996bytes/SHA256SUMS194bytes. All3 assets downloaded to/tmp/iddqueue-rc5-github-readback and bytes matched local exactfiles. Publisher pins version/candidate/hashes and remains manual; PyPI verification recorded below.

## PyPI and final acceptance

Signedpublisher383327f1a188382b95d619b3f25c7cae11d9e44d pushedmain. Actualremote workflow fetched viaGitHubAPI and byte-compared beforemanualdispatch. OIDCrun37588338940success: https://github.com/wa-pis/iddqueue/actions/runs/37588338940. PublisherTests37588308019success6/6, Documentation37588308159success; signedtagTests37588238718success.

PyPI https://pypi.org/project/iddqueue/0.13.0rc5/ version/license_expressionPostgreSQL and bothSHA256values matchedexactGitHub/localassets; JSONreadback saved/tmp/iddqueue-rc5-pypi.json. First immediate install had noRC5 in publicsimpleindex (metadataJSONalreadyavailable); no reupload. After30seconds cleanindexinstall succeeded.

Cleanvenv/tmp/iddqueue-rc5-index-check outsidecheckout: uvpipinstall --no-cache --default-indexhttps://pypi.org/simple/ iddqueue[binary,monitoring,sqlalchemy]==0.13.0rc5,9packages installed; pipcheckallcompatible, metadata/version/license verified, direct_url.jsonabsent, inspect.iscoroutinefunction confirms bothasyncmethods. Copied publishedrecipe executedusingpython-I withdedicatedPG14: businesscommit+actorresultpassed, workerstop and schema cleanup passed. No checkoutimport fallback.

PublicHTTPdocumentation rc-0.13.0rc5/recipes/api returnedRC5/asyncmethods/anchor. About description includes sync/asynctransactionalpublishing, homepage unchanged. RC1–RC4 untouched.

## Archive

Release change archived on 2026-10-07 after publication and final acceptance. All six tasks completed.

Final strict validation: 19/19 specs passed; active changes empty; git diff --check passed.
