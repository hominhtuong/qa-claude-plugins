# Makefile — __NAME__ automation. Shortcuts for the Maven commands you run most.
# Type `make` (or `make help`) for the list.
#
# Override vars (before or after the target):
#   ENV=staging|production   environment           (default staging)
#   HEADED=1                 run HEADED + slow (to watch / debug). Forces headed, ignores .env.
#   SLOWMO=<ms>              delay PER action when HEADED=1        (default 500)
#   PAUSE=<ms>               pause at the END of each test, HEADED=1 (default 1000)
#   BROWSER=chromium|firefox|webkit                (default chromium)
#   CLASS=, METHOD=          for the `test` / `method` targets
# Examples:
#   make regression                 # full regression, SERIAL (one browser, recommended)
#   make regression HEADED=1        # watch it: headed + 500ms/action + 1s/test
#   make smoke                      # critical-path subset
#   make test CLASS=LoginRegressionTest HEADED=1

ENV     ?= staging
BROWSER ?= chromium
HEADED  ?= 0
SLOWMO  ?= 500
PAUSE   ?= 1000
MVN     ?= mvn

# HEADED=1 forces watch mode (-D has highest precedence over .env); HEADED=0 passes nothing (CI/.env).
ifeq ($(HEADED),1)
HEAD := -DHEADLESS=false -DSLOWMO=$(SLOWMO) -DPAUSE_AFTER_TEST=$(PAUSE) -Dscreenshot.full.page=false
else
HEAD :=
endif

MVNFLAGS := -B -Denv=$(ENV) -Dbrowser=$(BROWSER) $(HEAD)

SMOKE_SERIAL      := suites/smoke-serial.xml
REGRESSION_SERIAL := suites/regression-serial.xml

.DEFAULT_GOAL := help
.PHONY: help setup compile clean smoke regression smoke-fast regression-fast test method report

help: ## Show this command list
	@echo "__NAME__ — test commands (ENV=$(ENV), BROWSER=$(BROWSER), HEADED=$(HEADED))"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Debug headed: HEADED=1 forces a visible browser + slows down; SLOWMO=<ms>/action, PAUSE=<ms>/test."

compile: ## Compile tests (no run) — green gate before commit
	$(MVN) -q -B test-compile

clean: ## Remove target/ + all run artifacts (results/reports/)
	$(MVN) -q -B clean
	rm -rf results/reports

# ---- Run suites (SERIAL — one browser for the whole run, recommended) ----

smoke: ## Smoke (critical path), SERIAL
	$(MVN) $(MVNFLAGS) test -DsuiteXmlFile=$(SMOKE_SERIAL)

regression: ## Full regression, SERIAL (use this by default)
	$(MVN) $(MVNFLAGS) test -DsuiteXmlFile=$(REGRESSION_SERIAL)

# ---- Parallel variants (faster but flakier on a shared account) ----

smoke-fast: ## Smoke in parallel (3 threads)
	$(MVN) $(MVNFLAGS) test -Psmoke

regression-fast: ## Regression in parallel (3 threads) — can be flaky
	$(MVN) $(MVNFLAGS) test -Pregression

# ---- Run one class / one method ----

test: ## Run one class:  make test CLASS=LoginRegressionTest
	@test -n "$(CLASS)" || (echo "Missing CLASS. e.g. make test CLASS=LoginRegressionTest"; exit 2)
	$(MVN) $(MVNFLAGS) test -Dtest=$(CLASS)

method: ## Run one method: make method CLASS=LoginRegressionTest METHOD=rejectWrongPassword
	@test -n "$(CLASS)" || (echo "Missing CLASS."; exit 2)
	@test -n "$(METHOD)" || (echo "Missing METHOD."; exit 2)
	$(MVN) $(MVNFLAGS) test -Dtest=$(CLASS)#$(METHOD)
