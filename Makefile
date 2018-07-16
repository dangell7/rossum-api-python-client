test:
	py.test

install:
	pip install rossum

install_dev:
	pip install -e .

uninstall:
	pip uninstall rossum

clean:
	rm -rf build/ dist/ rossum.egg-info/

build:
	python setup.py sdist
	python setup.py bdist_wheel --universal

# PyPI production

# twine - a tool for uploading packages to PyPI
publish:
	pip install twine
	twine upload dist/*
