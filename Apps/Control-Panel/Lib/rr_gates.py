# ==============================================================================
# FILE: Apps/Control-Panel/Lib/rr_gates.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Root Monitor wrapper for the execution gate file the broker enforces."""
from __future__ import annotations  # info: from __future__ import annotations
import importlib.util  # info: import importlib . util
from pathlib import Path  # info: from pathlib import Path

_GATES = Path("/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Automations/execution/gates.py")  # info: set _GATES
_spec = importlib.util.spec_from_file_location("rr_execution_gates", _GATES)  # info: set _spec
_mod = importlib.util.module_from_spec(_spec)  # info: set _mod
_spec.loader.exec_module(_mod)  # info: call _spec . loader . exec_module
load = _mod.load  # info: set load
save = _mod.save  # info: set save
lookup = _mod.lookup  # info: set lookup
set_gate = _mod.set_gate  # info: set set_gate
LABELS = [  # info: set LABELS
    ("modes.conversation", "Mode: conversation"),  # info: ( "modes.conversation" , "Mode: conversation" ) ,
    ("modes.work_order", "Mode: work order"),  # info: ( "modes.work_order" , "Mode: work order" ) ,
    ("modes.build", "Mode: build"),  # info: ( "modes.build" , "Mode: build" ) ,
    ("modes.diagnose", "Mode: diagnose"),  # info: ( "modes.diagnose" , "Mode: diagnose" ) ,
    ("modes.recovery", "Mode: recovery"),  # info: ( "modes.recovery" , "Mode: recovery" ) ,
    ("modes.deployment", "Mode: deployment"),  # info: ( "modes.deployment" , "Mode: deployment" ) ,
    ("steps.build.council_discovery", "Build: council discovery"),  # info: ( "steps.build.council_discovery" , "Build: council discovery" ) ,
    ("steps.build.question_send", "Build: question send"),  # info: ( "steps.build.question_send" , "Build: question send" ) ,
    ("steps.build.work_order_draft", "Build: work order draft"),  # info: ( "steps.build.work_order_draft" , "Build: work order draft" ) ,
    ("steps.build.handoff", "Build: handoff package"),  # info: ( "steps.build.handoff" , "Build: handoff package" ) ,
    ("steps.build.cursor_api", "Build: Cursor API"),  # info: ( "steps.build.cursor_api" , "Build: Cursor API" ) ,
    ("steps.build.file_modify", "Build: file modify"),  # info: ( "steps.build.file_modify" , "Build: file modify" ) ,
    ("steps.build.tests", "Build: tests"),  # info: ( "steps.build.tests" , "Build: tests" ) ,
    ("steps.build.execution_report", "Build: execution report"),  # info: ( "steps.build.execution_report" , "Build: execution report" ) ,
    ("steps.build.verification_report", "Build: verification report"),  # info: ( "steps.build.verification_report" , "Build: verification report" ) ,
    ("steps.build.commit", "Build: commit"),  # info: ( "steps.build.commit" , "Build: commit" ) ,
    ("steps.build.push", "Build: push"),  # info: ( "steps.build.push" , "Build: push" ) ,
    ("steps.build.merge", "Build: merge"),  # info: ( "steps.build.merge" , "Build: merge" ) ,
    ("steps.build.deploy", "Build: deploy"),  # info: ( "steps.build.deploy" , "Build: deploy" ) ,
    ("steps.recovery.inspect", "Recovery: inspect"),  # info: ( "steps.recovery.inspect" , "Recovery: inspect" ) ,
    ("steps.recovery.select_capability", "Recovery: select capability"),  # info: ( "steps.recovery.select_capability" , "Recovery: select capability" ) ,
    ("steps.recovery.run_existing_program", "Recovery: run existing program"),  # info: ( "steps.recovery.run_existing_program" , "Recovery: run existing program" ) ,
    ("steps.recovery.raise_attempt_cap", "Recovery: raise attempt cap"),  # info: ( "steps.recovery.raise_attempt_cap" , "Recovery: raise attempt cap" ) ,
]  # info: ]
