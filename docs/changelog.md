# Changelog

## 21.6.dev2

Date of release: *unreleased*

- \[bugfix\]: use posix slashes for target and benchmark names to avoid accidental
  newlines leading to crashes on Windows
- \[enhancement\]: added `dump` command to easily query the source code for any built-in
  task or target
- \[enhancement\]: force safety checks to run under the `format` task to avoid
  [occasional but bad skewing of the data](labels/format-task-danger)
- \[enhancement\]: verify that Black is actually available in the current environment
  before running any benchmarks (and emit a human readable error instead of the original
  long tracebacky error)
- \[maintenance\]: created initial test suite to make sure blackbench isn't broken on
  all supported platforms

## 21.6.dev1

Date of release: 14 June, 2021

Initial development version of blackbench. Unsurprisingly it is functional but extremely
limited. Windows support is actually straight up broken due to a bug :P
