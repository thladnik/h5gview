import h5py
import logging

from h5gview import core

log = logging.getLogger(__name__)


class H5File(core.File):

    def __init__(self, *args):
        core.File.__init__(self, *args)

        self._file = h5py.File(self.path, 'r')

    def __repr__(self):
        return f'H5File("{self.id}")'

    def read(self):
        self._root_group = H5Group(self, self._file['/'])


class H5Group(core.Group):

    def __init__(self, file, group: h5py.Group):
        core.Group.__init__(self, file)
        self._group = group
        self.name = self._group.name.split('/')[-1]
        log.info(f'Create {self} from {self._group} in {self.file}')

        # Set up
        self.groups = [H5Group(self.file, item) for item in group.values() if isinstance(item, h5py.Group)]
        self.datasets = [H5Dataset(self.file, item) for item in group.values() if isinstance(item, h5py.Dataset)]
        self.attributes = self._get_attributes()

    def __repr__(self):
        return f'Group("{self.id}")'

    def _get_attributes(self):
        return [core.Attribute(self.file,
                               name=name,
                               dtype=self._group.attrs[name].dtype,
                               shape=self._group.attrs[name].shape,
                               data=self._group.attrs[name])
                for name in self._group.attrs]

    def get(self):
        return {**{g.name: g for g in self.groups}, **{d.name: d for d in self.datasets}}

    def get_tree(self):
        return {**{g.name: g.get_tree() for g in self.groups}, **{d.name: d for d in self.datasets}}


class H5Dataset(core.Dataset):

    def __init__(self, file, dataset: h5py.Dataset):
        core.Dataset.__init__(self, file)
        self._dataset = dataset
        self.name = self._dataset.name.split('/')[-1]
        log.info(f'Create {self} from {self._dataset} in {self.file}')

        self.file.filegroup.add_dataset(self)

        # Set basic information
        self.shape = self._dataset.shape
        self.maxshape = self._dataset.maxshape
        self.dtype = self._dataset.dtype

    def _get_attributes(self):
        return [core.Attribute(self.file,
                               name=name,
                               dtype=self._dataset.attrs[name].dtype,
                               shape=self._dataset.attrs[name].shape,
                               data=self._dataset.attrs[name])
                for name in self._dataset.attrs]

    def __repr__(self):
        return f'Dataset("{self.id}")'