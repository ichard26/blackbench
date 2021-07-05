# Changelog

## 21.6.dev2

Date of release: *unreleased*

**Bugfixes & enhancements**:

- Use posix slashes for target and benchmark names to avoid accidental newlines leading
  to crashes on Windows
- Added `dump` command to easily query the source code for any built-in task or target
- Force safety checks to run under the `format` task to avoid
  [occasional but bad skewing of the data](labels/format-task-danger)
- Verify that Black is actually available in the current environment before running any
  benchmarks (and emit a human readable error instead of the original long tracebacky
  error)
- Arguments can now be passed to the underlying pyperf processes by adding `--` followed
  by such arguments. Useful for debugging stability or slowness issues.

**Project**:

- Created initial test suite to make sure blackbench isn't broken on all supported
  platforms
- Initial documentation including user guide and contributing docs have been written and
  are hosted on ReadTheDocs.

## 21.6.dev1

Date of release: 14 June, 2021

Initial development version of blackbench. Unsurprisingly it is functional but extremely
limited. Windows support is actually straight up broken due to a bug :P
