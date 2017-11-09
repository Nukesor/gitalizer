"""Helper functions for github api calls."""

def call_github_function(github_object: object, name: str, args: list):
    _try = 0
    tries = 3
    exception = None
    while _try <= tries:
        try:
            get_attr(github_object, 'name')(*args)
            return
        except RateLimitExceededException as e:
            # Wait until the rate limiting is reset
            resettime = github.rate_limiting_resettime
            resettime = datetime.datetime.fromtimestamp(resettime)
            delta = resettime - datetime.now()
            delta += datetime.timedelta(minutes=1)
            time.sleep(delta.total_seconds())

            _try += 1
            exception = e
            pass
