# tests/

**Owns:** smoke tests, one subfolder per top-level module, mirroring the tree
1:1 (`tests/core/`, `tests/fetch/`, `tests/alerts/`, `tests/hurricanes/`).

**Does NOT own:** fixtures that hit the live network by default — tests
should run offline against recorded fixtures unless explicitly marked
`@pytest.mark.live`.

**Depends on:** whatever module it's testing, nothing else.
