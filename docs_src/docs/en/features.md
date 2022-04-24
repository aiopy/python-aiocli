## AIOCLI features

**AIOCLI** provides you with the following:

### Native-based

- Full compatible with Python's [argparse module](https://docs.python.org/3/library/argparse.html). *Nothing new to learn.*

- Completely typed based on standard Python 3.6 [type hints](https://docs.python.org/3/library/typing.html). *Fewer bugs, IDEs friendly.*

### Async support

- Works and awaited through `run_app(...)` method like [AIOHTTP](https://github.com/aio-libs/aiohttp) library. *Easy to use.* 

- Allow set an [event loop](https://docs.python.org/3/library/asyncio-eventloop.html), by default `get_event_loop()`. *Better third party integrations.*

- Handle [signal’s life-cycle](https://docs.python.org/3/library/signal.html) using `CommandHook`s. *Great UNIX signals management.*

### Dependency Injection

- Always must be functions whether kind be "sync", [async](https://docs.python.org/3/reference/compound_stmts.html#async-def) or [yield](https://docs.python.org/3/reference/expressions.html#yield-expressions). *Solves several aio issues.*

- Each dependency can have dependencies like a "graph". *Avoid making a mess.*

- Each dependency allows [caching](https://docs.python.org/3/library/functools.html). *Better performance.*

### Serverless support

- Cloud providers: AWS Lambda, Azure Function and Google Cloud Function. *Go serverless.*

- Custom: Wrapping `run_app` function and changing default argument values. *Anything else?*

### State support

- Allow to have a container to share between commands. *No complications.*

### Test support

- Provides `TestCommander` and `TestClient` utilities. *No more excuses not to test.*

### Editor support

- in [Visual Studio Code](https://code.visualstudio.com):

![Visual Studio Code editor support](https://aiopy.github.io/python-aiocli/imgs/vscode-completion.png)

- in [PyCharm](https://www.jetbrains.com/pycharm/):

![PyCharm editor support](https://aiopy.github.io/python-aiocli/imgs/pycharm-completion.png)

