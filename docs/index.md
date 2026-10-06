# IDDQueue

IDDQueue provides a synchronous PostgreSQL broker and Results backend for [Dramatiq](https://dramatiq.io/). It uses Psycopg 3, JSONB, LISTEN/NOTIFY and session advisory locks, without an ORM or a separate broker service. Delivery is at least once: actors and callbacks must be idempotent.

One queue table stores messages and results; coordination, deduplication, queue control, attempts and schedules use separate tables. Notifications wake workers, which claim authoritative rows; startup and idle recovery also scan storage. Fixed interval scheduling polls due rows.

## Start here

Follow the [step-by-step walkthrough](walkthrough.md) to install the published RC, prepare PostgreSQL, start a worker and retrieve your first result. Each stage includes manual steps and commands.

Maintainers can [edit and deploy this site](docs-site.md) or follow the [PyPI publishing guide](publishing.md).

## Contents

- [Get Started](get-started.md)
- [Migration from dramatiq-pg](migration.md)
- [FastAPI integration](fastapi.md)
- [User Guide](user-guide.md)
- [Detailed recipes](recipes.md)
- [API Reference](api.md)
- [Deployment Guide](deployment-guide.md)
- [Compatibility and support](https://github.com/wa-pis/iddqueue/blob/main/SUPPORT.md)
- [Contributing](https://github.com/wa-pis/iddqueue/blob/main/CONTRIBUTING.md)
- [0.13.0rc3 release notes](rc-0.13.0rc3.md)
- [Release checks](release.md)
- [IDDQueue changelog](https://github.com/wa-pis/iddqueue/blob/main/CHANGELOG.md)
- [Historical upstream changelog](https://github.com/wa-pis/iddqueue/blob/main/docs/changelog.rst)
- [Why PostgreSQL](why.md)

[Source](https://github.com/wa-pis/iddqueue) and [issues](https://github.com/wa-pis/iddqueue/issues) are public. The 0.13.0rc3 prerelease is available on [PyPI](https://pypi.org/project/iddqueue/0.13.0rc3/). This fork preserves DALIBO's PostgreSQL [LICENSE](https://github.com/wa-pis/iddqueue/blob/main/LICENSE) and upstream credits in [README](https://github.com/wa-pis/iddqueue/blob/main/README.md).
