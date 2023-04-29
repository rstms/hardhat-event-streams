# make clean targets

.PHONY: clean-clean clean-build clean-pyc clean-test

# clean all
clean-clean:
	rm -rf build/
	find dist -not -name README.md -not -name dist -exec rm -f '{}' +
	rm -rf wheels/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

