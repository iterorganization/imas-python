import datetime
from pathlib import Path

import numpy as np

import imas
import imaspy


DBEntry = {
    "imas": imas.DBEntry,
    "imaspy": imaspy.DBEntry,
}
factory = {
    "imas": imas,
    "imaspy": imaspy.IDSFactory(),
}


def fill_slice(core_profiles, t):
    """Fill a time slice of a core_profiles IDS with generated data.

    Args:
        core_profiles: core_profiles IDS (either from IMASPy or AL HLI)
        t: time
    """
    core_profiles.ids_properties.homogeneous_time = 1  # HOMOGENEOUS
    core_profiles.ids_properties.comment = "Generated for the IMASPy benchmark suite"
    core_profiles.ids_properties.creation_date = datetime.date.today().isoformat()
    core_profiles.code.name = "IMASPy ASV benchmark"
    core_profiles.code.version = imaspy.__version__
    core_profiles.code.repository = (
        "https://git.iter.org/projects/IMAS/repos/imaspy/browse"
    )

    core_profiles.time = np.array([t])
    core_profiles.profiles_1d.resize(1)
    profiles_1d = core_profiles.profiles_1d[0]
    # Fill in grid coordinate
    N_GRID = 64
    profiles_1d.grid.rho_tor_norm = np.linspace(0, 1, N_GRID)
    gauss = np.exp(5 * profiles_1d.grid.rho_tor_norm**2)
    # Create some profiles
    noise = 0.8 + 0.4 * np.random.random_sample(N_GRID)
    profiles_1d.electrons.temperature = t * gauss * noise
    profiles_1d.electrons.density = t + gauss * noise
    ions = ["H", "D", "T"]
    profiles_1d.ion.resize(len(ions))
    profiles_1d.neutral.resize(len(ions))
    for i, ion in enumerate(ions):
        profiles_1d.ion[i].label = profiles_1d.neutral[i].label = ion
        profiles_1d.ion[i].z_ion = 1.0
        profiles_1d.ion[i].neutral_index = profiles_1d.neutral[i].ion_index = i + 1

        noise = 0.8 + 0.4 * np.random.random_sample(N_GRID)
        profiles_1d.ion[i].temperature = t * gauss * noise + i
        profiles_1d.ion[i].density = t + gauss * noise + i

        profiles_1d.neutral[i].temperature = np.zeros(N_GRID)
        profiles_1d.neutral[i].density = np.zeros(N_GRID)


class IncrementalConfig:
    # Configuration shared by IncrementalGet and IncrementalPut
    hlis = ["imas", "imaspy"]
    # Backends (only use persistent ones, MEMORY_BACKEND will fail some tests)
    backends = [
        imaspy.ids_defs.HDF5_BACKEND,
        # imaspy.ids_defs.MDSPLUS_BACKEND,
    ]

    params = [hlis, backends]
    param_names = ["HLI", "Backend ID"]

    N_slices = 128


class IncrementalPut(IncrementalConfig):
    def setup(self, hli, backend):
        path = str(Path.cwd() / f"DB-{hli}-{backend}")
        self.dbentry = DBEntry[hli](backend, "benchmark", 1, 1, path)
        self.dbentry.create()
        self.core_profiles = factory[hli].core_profiles()

    def teardown(self, hli, backend):
        self.dbentry.close()

    def time_generation(self, hli, backend):
        # Time generation of core profiles slices, as baseline for the time_put_slice
        for t in np.linspace(0, 1000, self.N_slices):
            fill_slice(self.core_profiles, t)

    def time_put_slice(self, hli, backend):
        for t in np.linspace(0, 1000, self.N_slices):
            fill_slice(self.core_profiles, t)
            self.dbentry.put_slice(self.core_profiles)


class IncrementalGet(IncrementalConfig):
    def setup_cache(self):
        hli = "imas"  # HLI used for pre-generating the data
        for backend in self.backends:
            path = str(Path.cwd() / f"DB-{backend}")
            self.dbentry = DBEntry[hli](backend, "benchmark", 1, 1, path)
            self.dbentry.create()
            self.core_profiles = factory[hli].core_profiles()
            for t in np.linspace(0, 1000, self.N_slices):
                fill_slice(self.core_profiles, t)
                self.dbentry.put_slice(self.core_profiles)
            self.dbentry.close()

    def setup(self, hli, backend):
        path = str(Path.cwd() / f"DB-{backend}")
        self.dbentry = DBEntry[hli](backend, "benchmark", 1, 1, path)
        self.dbentry.open()

    def time_get_slice(self, hli, backend):
        for t in np.linspace(0, 1000, self.N_slices):
            self.dbentry.get_slice("core_profiles", t, imas.imasdef.CLOSEST_INTERP)

    def time_get(self, hli, backend):
        self.dbentry.get("core_profiles")
