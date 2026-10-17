# Contributing

Keep changes reproducible and state which exact board, firmware version, wiring,
region and test conditions were used. A simulator or successful compile does not
count as a radio, power, thermal, fit or printer test.

Run `python3 tools/check.py`, `python3 -m unittest discover -s tests -p 'test_*.py'`,
the ESPHome validation/compile tool and the mechanical generator for changes
affecting those deliverables. Use `RF_CPP_SANITIZERS=1` for the native regression
harnesses. Preserve stable pin maps and
flag any change requiring rewiring. Submit changes through a pull request.

Use synthetic examples only. Never attach controller backups, Thread datasets,
Matter onboarding codes, household RF captures, API keys or private network details.
Do not redistribute vendor firmware unless its license expressly permits it.
