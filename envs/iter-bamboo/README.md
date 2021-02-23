This folder contains scipts to set up your environment on the ITER cluster.
At time of writing, the following hpc login nodes are known:
```
hpc-login0[1-5]
sdcc-login0[1-3]
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
These scripts can be used by Bamboo, preferably in order. Preferably keep order
intact. If scripts form a graph, there are two options:
- The script should not be ran in combination with another script:
    - Give them the same number
- The script should should be run after another script
    - Give them the (number + 1) of the script it can be run after
