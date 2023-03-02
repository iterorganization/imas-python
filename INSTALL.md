# ITER
Just to be sure, check if you don't have potentially conflicting modules loaded
```bash
module list
# No Modulefiles Currently Loaded.
```

Then clone and install IMASPy in user space
```bash
git clone ssh://git@git.iter.org/imas/imaspy.git
module load IMAS
pip install --user --upgrade tomli
cd imaspy
python setup.py build_DD # Build the DD. Might take a few minues
pip install --user --upgrade .
```

Test your installation by trying
```
cd ~
python -c "import imaspy; print(imaspy.__version__)"
```
which should return your just installed version number. The number is build by
setuptools from the `git describe` of the source repository.
