#!/usr/bin/env sh

set -e

_help() {
  echo "Usage:  $0 [OPTIONS] COMMAND

Commands:
  install                             Install Python dependencies
  build                               Build Python application
  build-docs                          Build Python application docs
  deploy                              Deploy Python application
  fmt                                 Format Python code
  security-analysis                   Analyze security of Python code
  static-analysis                     Analyze rules of Python code
  test [unit|integration|functional]  Run Python tests (default all suites)
  coverage                            Run Python test coverage
  clean                               Remove Python rubbish produced

Options:
  -h, --help      Show this help message and exit
  -v, --version   Show program's version number and exit"
}

_version() {
  awk '/^version.*=.*/ {gsub(/"/, "", $3); print($3)}' "pyproject.toml"
}

_install() {
  python3 -m pip install -r requirements-dev.txt
  pre-commit install --hook-type commit-msg || true
}

_build_docs() {
  python3 -m mkdocs build -f ./docs_src/mkdocs.yml -d ./../docs
}

_build() {
  python3 setup.py sdist bdist_wheel
  _build_docs
}

_deploy() {
  python3 -m twine upload dist/*
}

_fmt() {
  python3 -m autoflake --in-place --remove-all-unused-imports --remove-unused-variables --recursive "$project" tests
  python3 -m black "$project" tests
  python3 -m isort "$project" tests
}

_security_analysis() {
  python3 -m liccheck -r requirements-dev.txt
  python3 -m bandit -s B101,B311 -r "$project"
}

_static_analysis() {
  shellcheck pyscript.sh
  python3 -m mypy \
    --strict \
    --allow-subclassing-any \
    --allow-untyped-decorators \
    --no-warn-return-any \
    --follow-imports=skip \
    --ignore-missing-imports \
    --allow-any-generics \
    --cache-dir=var/cache/.mypy_cache \
    "$project"
  python3 -m pylint "$project"
}

_test() {
  python3 -m pytest "tests/$1"
}

_coverage() {
  python3 -m pytest --cov-report=html:var/log/.pytest_coverage --cov="${project}" --cov-fail-under=70 tests
  rm -rf .coverage &
}

_clean() {
  find . \( -name "__pycache__" -o -name "*.pyc" \) -print0 | xargs -0 rm -rf
  rm -rf build dist var
}

main() {
  project="$(awk '/^name.*=.*$/ {gsub(/"/, "", $3); print($3); exit}' "pyproject.toml")"
  function=$1

  test "$#" -ne 0 && shift 1
  test -z "$function" && function=help

  set -a
  tox_pyversion=$(grep "envlist" < "pyproject.toml"  | sed "s/[^0-9]*//")
  # shellcheck disable=SC1090,SC1091
  if [ -f "var/tox/py$tox_pyversion/bin/activate" ]; then . "var/tox/py$tox_pyversion/bin/activate"; fi;
  set +a

  export PYTHONPATH=.
  export PYTHONDONTWRITEBYTECODE=1
  export PYTHONUNBUFFERED=1

  # shellcheck disable=SC2269
  case "$function" in
  -h | --help | help) function=help ;;
  -v | --version | version) function=version ;;
  build-docs | build | deploy | install | fmt | security-analysis | static-analysis | test | coverage | clean) function=$(echo $function | sed 's/\-/\_/g') ;;
  *) echo >&2 "pyscript: '$function' is not a pyscript command." && exit 1 ;;
  esac

  "_$function" "$@"
}

main "$@"
