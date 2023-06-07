# Reproduction of versioning file systems

| System    | Status             |
| --------- | ------------------ |
| Copyfs    | :heavy_check_mark: |
| Gitfs     | :x:                |
| Nilfs     | :heavy_check_mark: |
| tux3      | :x:                |
| waybackfs | :heavy_check_mark: |

## Requirements

- `GNU parallel` (https://www.gnu.org/software/parallel/) - running all scripts at once
- `vagrant` - virtualization platform for tests (with plugins vagrant-cachier and vagrant-disksize)
- `virtualbox` - provider for vagrant
- `bash`
- `bonnie++` - bon_csv2html script for bonnie graph creation
- `python` - parsing results and creating graphs
- `fio`, `gnuplot` - fio2gnuplot script

## Running

- `make boxes` - generate and load custom vagrant boxes with all dependencies
- `make test` - run tests
