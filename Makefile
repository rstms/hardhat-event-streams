# top-level Makefile 
 
.PHONY: usage short-help pip update dev install uninstall run clean 

usage: short-help

### upgrade pip and friends
pip:
	pip install -U pip setuptools wheel

common_modules = seven-common seven-registry

update: depends-clean depends
	$(foreach mod,$(common_modules),pip install -f dist --upgrade $(mod))

### local install in editable mode for development
dev: update
	pip install --verbose --upgrade -f dist -e .[dev]

### install to the local environment from the source directory
install: update
	pip install --verbose -f dist .

### remove module from the local python environment
uninstall: pip
	pip uninstall -yqq $(module) $(common_modules)

### run api with dev environment
run:
	env PROFILE=streamsdev SERVICE=streams chamber-env streams --workers 1 -l INFO

### run api with dev environment in debug mode
run-debug:
	env PROFILE=streamsdev SERVICE=streams chamber-env env DEBUG=1 streams --debug --workers 1 -l DEBUG

### rebuild alembic database migration
dbinit:
	db-init

makefiles = $(wildcard make/*.mk)
include $(makefiles)

$(makefiles): 
	@:
