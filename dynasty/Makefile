# directories
WORKSPACE_DIR := workspace
EXPERIMENT_DIR := $(WORKSPACE_DIR)/experiments

# rules


all: run

run:
	bash $(EXPERIMENT_DIR)/experiment.sh

clean:
	@$(RM) -rf output* *.out *.log *.jani state_signatures.*

r: run
c: clean
