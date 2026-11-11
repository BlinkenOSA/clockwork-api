# clockwork_api
API for the Clockwork Archival Management System @ Blinken OSA

[![Build Status](https://www.travis-ci.org/BlinkenOSA/clockwork_api.svg?branch=development)](https://www.travis-ci.org/BlinkenOSA/clockwork_api)

LCSH endpoint tests mock Library of Congress responses so normal test runs do not
depend on that service. To run the separate live checks explicitly:

```sh
RUN_LCSH_LIVE_TESTS=1 python manage.py test authority.tests.test_lcsh_live
```

These checks require network access and may fail if LoC is unavailable or blocks
the runner. Upstream HTTP failures and request errors are logged by
`authority.views.lcsh_views` at warning level.
