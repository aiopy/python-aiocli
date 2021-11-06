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
