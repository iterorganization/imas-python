import imaspy


class ParseDDSuite:
    params = imaspy.dd_zip.dd_xml_versions()

    def setup(self, version: str) -> None:
        imaspy.dd_zip.dd_etree.cache_clear()

    def time_load_dd_etree(self, version: str) -> None:
        imaspy.dd_zip.dd_etree(version)


def timeraw_import_imaspy():
    return """
    import imaspy
    """


def timeraw_import_imas():
    return """
    import imas
    """
