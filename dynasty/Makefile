# directories
WORKSPACE_DIR := workspace
EXP_DIR := $(WORKSPACE_DIR)/experiments
EXP_SH := $(EXP_DIR)/experiment.sh
# rules


all: run

run:
	cp $(EXP_SH) $(EXP_DIR)/run.sh && bash $(EXP_DIR)/run.sh

clean:
	@$(RM) -rf output* *.out *.log *.jani state_signatures.*

r: run
c: clean

t1:
	cp $(EXP_SH) $(EXP_DIR)/t1.sh && bash $(EXP_DIR)/t1.sh
t2:
	cp $(EXP_SH) $(EXP_DIR)/t2.sh && bash $(EXP_DIR)/t2.sh
t3:
	cp $(EXP_SH) $(EXP_DIR)/t3.sh && bash $(EXP_DIR)/t3.sh
t4:
	cp $(EXP_SH) $(EXP_DIR)/t4.sh && bash $(EXP_DIR)/t4.sh

