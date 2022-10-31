## To remember

When altering buildroot/linux configuration remember to copy .config\* files into main dir.

## Requirements

- qemu
- docker
- gcc
- make
- expect

## Scripts

- `setup.sh` compile everything
- `test.sh` run tests inside qemu using expect program
- `clean.sh` cleans all generated files

## Reproduction status

_FAILED_ - tux3 throw errors during mount command
