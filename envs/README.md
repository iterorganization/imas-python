This folder contains scipts to set up your environment for multiple clusters.
For example on the ITER cluster we have the following loging nodes:
```
hpc-login0[1-5]  # "HPC-like"
sdcc-login0[1-3]  # "SDCC-like"
```
We prefix environment scripts with the following numbers:
| number | description      |
| ------ | ---------------- |
|   0x   | Global cluster   |
|   1x   | Python specific  |
|   2x   | IMAS classic     |
|   3x   | IMASPy specific  |
|   4x   | Actors           |
|   5x   | Workflow         |
|   7x   | Testing          |
|   8x   | Documentation    |
|   9x   | Cleaning         |
These scripts can be used in Bamboo and in the shell, preferably in order.
Try to keep the order intact when adding scripts. If scripts form a graph, there are two options:
- The script should not be ran in combination with another script:
    - Give them the same number
- The script should should be run after another script
    - Give them the (number + 1) of the script it can be run after

# Default bash flags
For the bash starters, we use the following flags, see https://tldp.org/LDP/abs/html/options.html
```
-v          verbose       Print each command to stdout before executing it
-x          xtrace        Similar to -v, but expands commands
-e          errexit       Abort script at first error, when a command exits with non-zero status (except in until or while loops, if-tests, list constructs)
-u          nounset       Attempt to use undefined variable outputs error message, and forces an exit
-f          noglob        Filename expansion (globbing) disabled
-o pipefail pipe failure  Causes a pipeline to return the exit status of the last command in the pipe that returned a non-zero return value.
```
