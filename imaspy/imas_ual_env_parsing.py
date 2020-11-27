# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
def parse_UAL_version_string(string):
    """Parses a UAL_VERSION string

    Parses the UAL_VERSION to IMASPy format. By convention, the
    UAL_VERSION string is generated by git-describe and edited.
    In our case for patch versions 'symver', e.g. '4.8.2'. For
    development versions it is 'symver-steps_from_symver-gcommit', e.g.
    '4.8.2-2-g1fffb6bf'

    Args:
      - string: The UAL_VERSION string.

    Returns:
      - ual_symver: The symversion of the passed UAL_VERSION
      - steps_from_version: Amount of steps the development version is from symver
      - ual_commit: The exact commit of the passed string. Symver for release version.

    """

    if "-" in string:
        ual_symver, micropatch = string.split("-", 1)
        steps_from_version, commitspec = micropatch.split("-", 2)
        ual_commit = commitspec[1:]
    else:
        ual_symver = string
        steps_from_version = "0"
        ual_commit = ual_symver
    return ual_symver, steps_from_version, ual_commit


def sanitise_UAL_symver(ual_symver):
    """Sanitizes a ual_symver for use in packages"""
    return ual_symver.replace(".", "_")


def build_UAL_package_name(sanitised_UAL_symver, ual_commit):
    """Build the package name for UAL Python packages"""
    return "imas._ual_lowlevel"

    if "." in ual_commit:
        # Release package
        return "ual_{!s}._ual_lowlevel".format(sanitised_UAL_symver)
    else:
        # 'dev' or 'in-between' package
        return "ual_{!s}_{!s}._ual_lowlevel".format(sanitised_UAL_symver, ual_commit)