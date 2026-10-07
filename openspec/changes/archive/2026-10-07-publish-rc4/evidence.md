# RC4 release evidence — 2026-10-07

Security/readiness changes завершены/архивированы; signed190932d, de9f077,227df9f и их actualCI6/6success зафиксированы в соответствующих evidence. Standard security scan28044df завершён:2findingsmedium/low, нетhigh/critical среди validatedfindings, runtime/scriptsCI/executabletests/examples reviewed; remainingprose/dependencyfeeds partial. Daybreaknotgranted. Remediation regression/full188tests подтверждены; это не повторный полный securityscan послеpatch.

Полный scripts/check_release.sh exit0:Python3.13.14/PostgreSQL14.20(port55433),188passed59.58s; locked sync/pipcheck/Ruff/docsstrict/checkdocs/OpenSpec/build/LICENSE; isolated base/monitoring/sqlalchemy installation и exact quickstart passed. Version0.13.0rc4, uv.lock updated. Build содержит исходники/package SQL/LICENSE, прежние dist/rc3 не изменялись.

WheelSHA256 d5a5858677c31b6017ccdbf57fb1c31acd0a68c68f4e7babbe9ff11efa3e442b
SdistSHA256 58cfdb591bad5fd23d9be32223488dbfaa5d4c9098bf8662b65ef9c4f9cbee84

Candidate SHA, remoteCI/tag/GitHub/PyPI publication/indexinstallation pending. Не считать подготовку публикацией.

Предварительный candidatea529e5e: Tests37555454492initial5/6(two lock-release failures), rerunfailedfinal6/6success. Rerun НЕ снимает найденный дефект: forcedSeqScanPG18.6 воспроизвёл50лишних acquisitions; forcedSeqScan regressions доfix2failedнаPG14/18. Исправление fix-single-claim-lock-acquisition добавлено до tag/publication; прежние candidateSHA/hashes НЕ будут публиковаться.

Final local candidate послеsingle-claim-lock fix: fullgateexit0,190passed58.58s(PG14.20/Python3.13.14), PG18targeted38passed/InitPlan/noextraunlock. Всеостальныеgatechecks/profiles/quickstart/LICENSEpass. FinalwheelSHA2561fd710c4c8a425c736a70812b787ec9145a5e7be45633effc38aa6f9c0fa8938; finalsdistSHA25625a03c41578af2b74a1c8da6f04d7d843152f749e6cbe89e7ad60e9135291f8b. ПрежниенеопубликованныеRC4assets пересобраны доtag/upload; publishedRC1/2/3 неизменны.

Finalcandidate signed6eb5aac4a1a11472d575c3e4e425e5a2285d825a pushmain. Finalwheel вfresh/tmp/iddqueue-rc4-wheel-venv [binary,monitoring,sqlalchemy] installed outsidecheckout; -I combined acceptance наPG18.6: SQLAlchemycommit/business/task/result, rollbackbothabsent, billing/shipping.eu nativeResults, malformedNOTIFYsame sessions, forcedSeqScan/alternate durableUUID/ACKsinglelock,3domain snapshots passedexit0. Temporaryschema dropped и worker/pool/engine stopped. Wheelmodulebytes/sdistREADME+metadata equal signedcandidate source. Tests37556241736 pending; Documentation37556241590success.

Последнийlocalreleasegate с correlatedcrash/ACK tests exit0:191passed57.97s и всеpackaging/docs/lockchecks/profiles/quickstartpass. Finalwheelhash1fd710c4c8a425c736a70812b787ec9145a5e7be45633effc38aa6f9c0fa8938; sdist25a03c41578af2b74a1c8da6f04d7d843152f749e6cbe89e7ad60e9135291f8b. Candidate6eb5aacCI5/6failedиз-заoldcrashoracle; он supersededtest-onlycandidate, tag/uploadне выполнялись.

Finalcandidateca68594f035b46a4b21e0a8a9ae4ad50da6c6d4f signed/pushed; Tests37557035497firstattemptactual6/6success, Documentation37557035482success. Lock/crashchangesarchived; fixedpublisherworkflowtargetca68594 andfinalhashesverified. Publicrc4/sqlalchemy/customrecipes docscheckedHTTP200/expectedcontent. Tag/publicationpending.

Signedtagv0.13.0rc4 verifiedgoodSSHsignature, points toca68594; pushed. GitHubhttps://github.com/wa-pis/iddqueue/releases/tag/v0.13.0rc4 isPrereleasetrue/targetCommitishca68594; assetswheel36247bytes/sdist27315bytes/SHA256SUMS194bytes. Downloadreadbackbothhashesequalfinal1fd710c4/25a03c41, checksumsfilebytesmatch. PyPIpending.

Publisher signedcommitd2732483b609724d675fe2a07344878f4e573caf pushmain. PyPI Trusted Publishing37557486173success, exactdownloadedGitHubassets validatedwithoutrebuild. PublisherTests37557474420actual6/6success/Documentation37557474421success. SignedtagpushTests37557356139actual6/6success also verified.

PyPIhttps://pypi.org/project/iddqueue/0.13.0rc4/ JSONversion0.13.0rc4/LicenseExpressionPostgreSQL/twoexacthashesmatchfinalassets. Freshindexinstall/tmp/iddqueue-rc4-index-check [binary,monitoring,sqlalchemy] from https://pypi.org/simple/ succeeded(no direct_url.json), outsidecheckoutimports/version/license/Domain/SQLAlchemy/domainmetrics and uvpipcheckpassed. Первое immediateindexinstall ещёнеразрешилversion; publicsimpleindexRC4confirmed и explicitindexretrypassed. Первыйquickstartзапускбезdedicatedguard rejectedbeforeDBwork; correctguardrerunpending.

Correctguardcleanindexquickstart exit0: sixstorage tables/enqueue/actorresult5, isolatedquickstartschema removed; nativeworker/poolstopped. PyPIcleaninstallationacceptance complete. GitHubreleasebody nowlinksPyPI/OIDC37557486173, readbackconfirmed. Release0.13.0rc4achieved; archivalactionpendingonly.

Releasechangeархивирован2026-10-07; allsix tasks complete, roadmap/config synchronized.
