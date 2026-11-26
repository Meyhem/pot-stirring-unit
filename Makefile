# Pot stirrer – build + check
#
#   make            build every printable STL into stl/ (only what changed)
#   make check      mesh validity of all STLs + geometry fit checks
#   make prune      delete STLs in stl/ that are not current parts
#   make images     re-render the README images
#   make circuit    simulate the motor power stage (ngspice) + draw its schematic
#   make all-in     everything above, in order (what to run after each iteration)
#   make rebuild    force re-export of every STL
#
# Add a new printable part: add it to GEARBOX_PARTS or a rule below.

OPENSCAD ?= openscad
PYTHON   ?= python3
BED      ?= 220 220 250

GEARBOX_PARTS := housing_a housing_b gear_in gear_out spacer
MOUNT_PARTS   := motor_mount_one_piece

STLS := $(GEARBOX_PARTS:%=stl/%.stl) $(MOUNT_PARTS:%=stl/%.stl)

.PHONY: stl check check-stl check-fit prune images all-in rebuild circuit sim schematic
.DEFAULT_GOAL := stl

stl: $(STLS)

# export to a temp file and move it into place, so a failed export never leaves
# a broken STL behind; --hardwarnings makes any OpenSCAD warning fail the build
define export
	@mkdir -p stl
	@echo "export  $@"
	@$(OPENSCAD) --hardwarnings -o $@.tmp.stl -D 'part="$(1)"' $(2) > $@.log 2>&1 \
		|| { cat $@.log; rm -f $@.log $@.tmp.stl; exit 1; }
	@grep -q "Simple: *yes" $@.log || { cat $@.log; echo "$@: not a simple solid"; rm -f $@.log $@.tmp.stl; exit 1; }
	@rm -f $@.log
	@if [ -f $@ ] && $(PYTHON) tools/stl_same.py $@ $@.tmp.stl; then \
		echo "        (geometry unchanged, keeping the old file)"; rm -f $@.tmp.stl; touch $@; \
	else mv $@.tmp.stl $@; fi
endef

$(GEARBOX_PARTS:%=stl/%.stl): stl/%.stl: angled_gearbox.scad common.scad
	$(call export,$*,angled_gearbox.scad)

stl/motor_mount_one_piece.stl: motor_mount.scad common.scad
	$(call export,mount,motor_mount.scad)

check: check-stl check-fit

check-stl: $(STLS)
	@$(PYTHON) tools/check_stl.py --bed $(BED) $(STLS)

check-fit:
	@$(PYTHON) tools/check_fit.py

prune:
	@for f in stl/*.stl; do \
		case " $(STLS) " in *" $$f "*) ;; *) echo "remove  $$f"; rm -f "$$f";; esac; \
	done

images:
	./render_images.sh

# ---- electronics (electronics/): ngspice + a local venv from requirements.txt
VENV := electronics/.venv
STAMP := $(VENV)/.installed

$(STAMP): electronics/requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q -r electronics/requirements.txt
	@touch $(STAMP)

sim: $(STAMP)
	@command -v ngspice >/dev/null || { echo "ngspice not found (apt install ngspice)"; exit 1; }
	@cd electronics && .venv/bin/python sim.py > /dev/null \
		|| { cat sim_results.md; echo "circuit checks FAILED"; exit 1; }
	@grep -c "PASS" electronics/sim_results.md | xargs printf "circuit checks: %s PASS\n"

schematic: $(STAMP)
	@cd electronics && .venv/bin/python schematic.py

circuit: sim schematic

all-in: stl prune check images circuit

rebuild:
	@touch common.scad
	@$(MAKE) --no-print-directory stl
