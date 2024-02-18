set -ex

mypy --disallow-untyped-defs --disallow-incomplete-defs kicadet
python3 -m unittest -v kicadet.tests
python3 example/example.py
