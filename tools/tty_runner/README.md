# tty_runner

## Description

Utility to execute shell commands in buildroot-powered
project.

## Build

```bash
make
```

## Usage

Issue help command for full options
`./build/src/tty --help`

Example

```bash
./build/src/tty --path-to-makefile ../../fs/nilfs-dedup --command-list commands/dedup.sh --output-file tty_output_dedup.log
./build/src/tty --path-to-makefile ../../fs/nilfs-dedup --command-list commands/remount.sh --output-file tty_output_remount.log
```