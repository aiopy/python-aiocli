## AIOCLI funcionalidades

**AIOCLI** provides you with the following:

### Integración nativa

- Totalmente compatible con el [módulo argparse](https://docs.python.org/3/library/argparse.html) de Python. *Nada nuevo que aprender.*

- Completamente tipado basado en el estándar de Python 3.6 [type hints](https://docs.python.org/3/library/typing.html). *Menos bugs, adaptado a los IDEs.*

### Soporte Asíncrono

- Funciona y se espera gracias al método `run_app(...)` como el de la librería [AIOHTTP](https://github.com/aio-libs/aiohttp). *Fácil de usar.* 

- Permite establecer tu [event loop](https://docs.python.org/3/library/asyncio-eventloop.html), por defecto es `get_event_loop()`. *Mejor integración con terceros.*

- Maneja las [signal’s life-cycle](https://docs.python.org/3/library/signal.html) utilizando los `CommandHook`. *Genial manejo de las señales UNIX.*

### Inyección de Dependencias

- Siempre deben de ser funciones "sync", [async](https://docs.python.org/3/reference/compound_stmts.html#async-def) o [yield](https://docs.python.org/3/reference/expressions.html#yield-expressions). *Soluciona varios problemas con aio.*

- Cada dependencia puede a su vez tener dependencias como un "grafo". *Evita liarla parda.*

- Cada dependencia permite [caching](https://docs.python.org/3/library/functools.html). *Increíble rendimiento.*

### Soporte para Serverless

- Proveedores Cloud: AWS Lambda, Azure Function y Google Cloud Function. *Go serverless.*

- A medida: Decorando la función `run_app` y cambiando los valores de los argumentos por defecto. *¿Algo más?*

### Soporte para Tests

- Provee `TestCommander` y `TestClient` como utilidades. *No hay más excusas para no hacer tests.*

### Soporte para Editores

- en [Visual Studio Code](https://code.visualstudio.com):

![Visual Studio Code editor support](https://aiopy.github.io/python-aiocli/imgs/vscode-completion.png)

- en [PyCharm](https://www.jetbrains.com/pycharm/):

![PyCharm editor support](https://aiopy.github.io/python-aiocli/imgs/pycharm-completion.png)

