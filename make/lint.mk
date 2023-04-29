# python lint makefile

.fmt: $(python_src)
	isort $(src_dirs)
	black -t py310 $(src_dirs)
	flake8 --max-line-length 135 $(src_dirs)
	touch $@

### format source and lint
fmt:	.fmt

### vim autofix
fix:
	fixlint $(src_dirs)

lint-clean:
	rm -f .black .flake8 .errors .fmt

lint-sterile:
	@:
