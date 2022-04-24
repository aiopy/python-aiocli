- con [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html):

```python
from aiocli.commander import Application
from aiocli.commander_app_wrappers import aws_run_app

app = Application()

def _parser(event, context) -> list[str]:
    pass

handler = aws_run_app(app, parser=_parser)
```

- con [Azure Function](https://docs.microsoft.com/azure/azure-functions/functions-reference-python):

```python
from aiocli.commander import Application
from aiocli.commander_app_wrappers import az_run_app

app = Application()

def _parser(req, context) -> list[str]:
    pass

handler = az_run_app(app, parser=_parser)
```

- con [Google Cloud Function](https://cloud.google.com/functions/docs/concepts/python-runtime):

```python
from aiocli.commander import Application
from aiocli.commander_app_wrappers import gcp_run_app

app = Application()

def _http_parser(request) -> list[str]:
    pass

http_handler = gcp_run_app(app, parser=_http_parser)

def _event_parser(event_or_data, context) -> list[str]:
    pass

event_handler = gcp_run_app(app, parser=_event_parser)
```

- con [Alibaba Cloud Function Compute](https://www.alibabacloud.com/help/en/function-compute/latest/programming-languages-python):

```python
from aiocli.commander import Application
from aiocli.commander_app_wrappers import alibaba_run_app

app = Application()

def _http_parser(environ, start_response) -> list[str]:
    pass

http_handler = alibaba_run_app(app, parser=_http_parser)

def _event_parser(event, context) -> list[str]:
    pass

event_handler = alibaba_run_app(app, parser=_event_parser)
```

- con [Oracle Cloud Function](https://www.oracle.com/cloud-native/functions/):

```python
from aiocli.commander import Application
from aiocli.commander_app_wrappers import oracle_run_app

app = Application()

def _parser(ctx, data) -> list[str]:
    pass

handler = oracle_run_app(app, parser=_parser)
```
