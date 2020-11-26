# directories
WORKSPACE_DIR := workspace
LOG_DIR := $(WORKSPACE_DIR)/log
EXP_SH := execute.sh

# rules

CORE := 0

all: run

run:
	$(eval RUN_SH := $(LOG_DIR)/run_$(CORE).sh)
	@cp $(EXP_SH) $(RUN_SH)
	@bash $(RUN_SH) $(CORE)

clean:
	@$(RM) output* *.out *.log *.jani state_signatures.* $(LOG_DIR)/*


r: run
c: clean

c1:
	@$(MAKE) --no-print-directory run CORE=1
c2:
	@$(MAKE) --no-print-directory run CORE=2
c3:
	@$(MAKE) --no-print-directory run CORE=3
c4:
	@$(MAKE) --no-print-directory run CORE=4

test:
	./test.sh
