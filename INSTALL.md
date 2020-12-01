# ITER
```bash
git clone ssh://git@gitlab.com/klimex/imaspy.git
module load IMAS
pip install --user --upgrade setuptools wheel gitpython numpy pytest ipython cython
cd imaspy
python setup.py # wait a minute or two

python -m pytest
```


and later:
```
pip install --user imaspy
```
