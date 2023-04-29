### create a new github release

.release: $(wheel)
ifeq "$(version)" "$(subst v,,$(shell gh -R $(GITHUB_ORG)/$(project) release view --json name --jq .name))"
	@echo version $(version) is already released
else
	gh release create v$(version) --generate-notes --target master;
	gh release upload v$(version) $(wheel);
endif
	@touch $@

release: .release


release-clean:
	rm -f .release


release-sterile:
	@:
