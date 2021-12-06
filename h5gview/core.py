from __future__ import annotations
import logging
import os
from typing import List, Dict, Union, Any
import uuid
import h5py

log = logging.getLogger(__name__)

class FileGroup:

    filegroup_register = []

    def __init__(self, filelist=None):

        self.files: Dict[str, H5File] = {}
        self.id = str(uuid.uuid4())
        log.info(f'Create FileGroup("{self.id}")')

        self.filegroup_register.append(self)

        if filelist is not None:
            for file in filelist:
                self.attach_file(file)

    def __repr__(self):
        return f'FileGroup("{self.id}")'

    def attach_file(self, file):
        if file in self.files:
            log.warning(f'{file} already attached to {self}')
            return

        if isinstance(file, H5File):
            self.files[file.id] = file
            file.attach_to_filegroup(self)
            file.create_tree()
        elif isinstance(file, str):
            self.attach_file(H5File(file))
        else:
            log.warning(f'Provided file argument {file} is not compatible')
            return

    def _add_instance(self):
        self.__class__.filegroup_register.append(self)

    def get_tree(self) -> Dict[str, Any]:
        toplevel: Dict[str, dict] = {}
        for file in self.files.values():
            toplevel[file.name] = file.get_tree()

        return toplevel


class H5File:

    def __init__(self, path):
        self.id = str(uuid.uuid4())
        log.info(f'Create {self} from {path}')

        self.path: str = os.path.abspath(path)
        self.name = self.path.split('/')[-1]
        self._file = h5py.File(path, 'r')

        self.filegroup = None
        self._root_group = None

    def __repr__(self):
        return f'H5File("{self.id}")'

    def __new__(cls, path, *args, **kwargs):
        path = os.path.abspath(path)
        if os.path.exists(path):
            log.info(f'Open file "{path}"')
            return super(H5File, cls).__new__(cls, *args, **kwargs)

        log.warning(f'File on path "{path}" can not be opened. It does not exist')
        return None

    def attach_to_filegroup(self, filegroup: FileGroup):
        log.info(f'Attach {self} to {filegroup}')
        self.filegroup = filegroup

    def create_tree(self):
        self._root_group = H5Group(self, self._file['/'])

    def get_tree(self):
        return self._root_group.get_tree()


class H5Group:

    def __init__(self, file: H5File,  group: h5py.Group):
        self.id = str(uuid.uuid4())
        self.file = file
        self._group = group
        self.name = self._group.name.split('/')[-1]
        log.info(f'Create {self} from {self._group} in {self.file}')

        # Set up
        self.groups = [H5Group(self.file, item) for item in group.values() if isinstance(item, h5py.Group)]
        self.datasets = [H5Dataset(self.file, item) for item in group.values() if isinstance(item, h5py.Dataset)]

    def __repr__(self):
        return f'Group("{self.id}")'

    def get_tree(self):
        return {**{g.name: g.get_tree() for g in self.groups}, **{d.name: d for d in self.datasets}}


class H5Dataset:

    def __init__(self, file, dataset: h5py.Dataset):
        self.id = str(uuid.uuid4())
        self.file = file
        self._dataset = dataset
        self.name = self._dataset.name.split('/')[-1]
        self.attrs = self._dataset.attrs
        log.info(f'Create {self} from {self._dataset} in {self.file}')

    def __repr__(self):
        return f'Dataset("{self.id}")'


if __name__ == '__main__':
    f1 = H5File('../sample/h5ex_d_rdwr.h5')
    f2 = H5File('../sample/h5ex_d_rdwr.h51')