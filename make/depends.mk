# python dependency wheels


dep_wheels = $(foreach depmod,$(common_modules),$(call github-wheel,$(depmod)) )

.depends: $(dep_wheels)
	$(foreach depmod,$(common_modules),$(call github-download,$(depmod));)
	@touch $@
	
depends: .depends

depends-clean: dist-clean
	rm -f .depends

depends-sterile:
	@:

depends-ls:
	@$(foreach wheel,$(dep_wheels),ls -l $(wheel);)

github-wheel = dist/$(shell gh -R $(GITHUB_ORG)/$(1) release view --json assets --jq '.assets[0].name')
github-download = gh -R $(GITHUB_ORG)/$(1) release download -D dist -p '*.whl'

