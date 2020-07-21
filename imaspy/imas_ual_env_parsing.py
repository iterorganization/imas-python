def parse_UAL_version_string(string):
    if '-' in string:
        ual_patch_version, micropatch = string.split('-', 1)
        steps_from_version, commitspec = micropatch.split('-', 2)
        ual_commit = commitspec[1:]
    else:
        ual_patch_version = string
        steps_from_version = '0'
        ual_commit = string
    return ual_patch_version, steps_from_version, ual_commit

def sanitise_UAL_patch_version(ual_patch_version):
    return ual_patch_version.replace('.', '_')

def build_UAL_package_name(safe_ual_patch_version, ual_commit):
    if '.' in ual_commit:
        # Release package
        return "ual_{!s}._ual_lowlevel".format(safe_ual_patch_version)
    else:
        # 'dev' or 'in-between' package
        return "ual_{!s}_{!s}._ual_lowlevel".format(safe_ual_patch_version, ual_commit)
