import pytest

from imaspy.dd_helpers import *


# TODO: Write tests!
#def prepare_data_dictionaries():
#def get_saxon():
#def find_saxon_jar():

# Quadruplets of (cluster, module, real path, name)
saxon_binary_quadruplets = (
    ("SDCC", "Saxon-HE/10.3-Java-1.8", "/work/imas/opt/EasyBuild/software/Saxon-HE/10.3-Java-1.8/saxon-he-10.3.jar", "saxon-he-10.3.jar"),
    ("SDCC", "Saxon-HE/10.3-Java-11", "/work/imas/opt/EasyBuild/software/Saxon-HE/10.3-Java-11/saxon-he-10.3.jar", "saxon-he-10.3.jar"),
    ("HPC",  "Saxon-HE/9.7.0.14-Java-1.6.0_45", "/work/imas/opt/EasyBuild/software/Saxon-HE/9.7.0.14-Java-1.6.0_45/saxon9he.jar", "saxon9he.jar"),
    ("HPC",  "Saxon-HE/9.7.0.4-Java-1.7.0_79", "/work/imas/opt/EasyBuild/software/Saxon-HE/9.7.0.4-Java-1.7.0_79/saxon9he.jar", "saxon9he.jar"),
    ("HPC",  "Saxon-HE/9.7.0.21-Java-1.8.0_162", "/work/imas/opt/EasyBuild/software/Saxon-HE/9.7.0.21-Java-1.8.0_162/saxon9he.jar", "saxon9he.jar"),
    ("HPC",  "Saxon-HE/9.9.1.7-Java-13", "/work/imas/opt/EasyBuild/software/Saxon-HE/9.9.1.7-Java-13/saxon9he.jar", "saxon9he.jar"),
    ("HPC",  "Saxon-HE/10.3-Java-11", "/work/imas/opt/EasyBuild/software/Saxon-HE/10.3-Java-11/saxon-he-10.3.jar", "saxon-he-10.3.jar"),
)

saxon_nonmatches = (
    "/work/imas/opt/EasyBuild/software/Saxon-HE/10.3-Java-11/saxon-he-test-10.3.jar",
)


# find_saxon_bin tries to find saxon in the CLASSPATH env variable
# It is thus per definition environment dependent
def test_empty_classpath(monkeypatch):
    monkeypatch.setenv("CLASSPATH", "")
    saxon_jar_path = find_saxon_classpath()
    assert saxon_jar_path is None


@pytest.mark.parametrize("cluster,module,path,name", saxon_binary_quadruplets)
def test_classpath(monkeypatch, cluster, module, path, name):
    monkeypatch.setenv("CLASSPATH", path)
    saxon_jar_path = find_saxon_classpath()
    assert saxon_jar_path == path


@pytest.mark.parametrize("path", saxon_nonmatches)
def test_classpath_do_not_match(monkeypatch, path):
    monkeypatch.setenv("CLASSPATH", path)
    saxon_jar_path = find_saxon_classpath()
    assert saxon_jar_path is None


# TODO: Write tests!
#def find_saxon_bin():
#def download_saxon():
#def get_data_dictionary_repo():
#def build_data_dictionary():
