# Reproduction of versioning file systems

| System    | Status             |
| --------- | ------------------ |
| Copyfs    | :heavy_check_mark: |
| Gitfs     | :x:                |
| Nilfs     | :heavy_check_mark: |
| tux3      | :x:                |
| waybackfs | :heavy_check_mark: |

## Requirements

- `bashful` (https://github.com/wagoodman/bashful) - running all scripts at once
- `vagrant` - virtualization platform for tests
- `virtualbox` - provider for vagrant
- `bash`
- `bonnie++` - bon_csv2html script for graphs creation

## Running

- `make boxes` - generate and load custom vagrant boxes with all dependencies
- `make test` - run tests using `__test_template*` files
