from __future__ import annotations
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Union, Any, Type, Tuple
import uuid
import h5py
import numpy as np

log = logging.getLogger(__name__)


class FileGroup:

    filegroup_register = []

    def __init__(self, filelist=None):

        self.files: Dict[str, File] = {}
        self.datasets: List[Dataset] = []
        self.id = str(uuid.uuid4())
        log.info(f'Create FileGroup("{self.id}")')

        self.filegroup_register.append(self)

        if filelist is not None:
            for file in filelist:
                self.attach_file(file)

    def __repr__(self):
        return f'FileGroup("{self.id}")'

    def _add_instance(self):
        self.__class__.filegroup_register.append(self)

    def add_dataset(self, dataset: Dataset):
        self.datasets.append(dataset)

    def attach_file(self, file):
        if file in self.files:
            log.warning(f'{file} already attached to {self}')
            return

        if isinstance(file, File):
            self.files[file.id] = file
            file.attach_to_filegroup(self)
            file.read()
        elif isinstance(file, str):
            self.attach_file(FileFactory.open_file(file))
        else:
            log.warning(f'Provided file argument {file} is not compatible')
            return

    def get_tree(self) -> Dict[str, Any]:
        toplevel: Dict[str, dict] = {}
        for file in self.files.values():
            toplevel[file.name] = file.get_tree()

        return toplevel


class Item(ABC):
    def __init__(self):
        self.id: str = str(uuid.uuid4())
        self._name: str = None
        self._path: str = None
        self._attributes: List[Attribute] = []

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @property
    def attributes(self) -> List[Attribute]:
        return self._attributes

    @attributes.setter
    def attributes(self, attributes):
        self._attributes = attributes


class File(Item):

    def __init__(self, path):
        Item.__init__(self)
        log.info(f'Create {self} from {path}')

        self.path = os.path.abspath(path)
        _, self.name = os.path.split(self.path)
        self._file = None
        self.filegroup = None
        self._root_group = None

    def attach_to_filegroup(self, filegroup: FileGroup):
        log.info(f'Attach {self} to {filegroup}')
        self.filegroup = filegroup

    def get(self):
        return self._root_group

    def get_tree(self):
        return self._root_group.get_tree()

    @abstractmethod
    def read(self):
        pass


class FileFactory:

    file_types: Dict[str, Type[File]] = {}
    known_extensions: List[str] = []

    @classmethod
    def open_file(cls, path: str):
        path = os.path.abspath(path)
        log.info(f'Open file on path "{path}"')

        if not os.path.exists(path):
            log.warning(f'File does not exist')
            return None

        path_to, filename = os.path.split(path)
        EXT = filename.split('.')[-1].upper()
        if EXT not in cls.known_extensions:
            log.warning(f'Unkown file extension "{EXT}"')
            return None

        return cls.file_types[EXT](path)

    @classmethod
    def add_extension(cls, ext: str, file_type: Type[File]):
        EXT = ext.upper()
        if EXT in cls.known_extensions:
            log.warning(f'Can not add file type {file_type} for extension {EXT}. Extension already in list')
            return

        log.info(f'Add extension {EXT} for file type {file_type}')
        cls.file_types[EXT] = file_type
        cls.known_extensions.append(EXT)

    @classmethod
    def add_extensions(cls, extensions: Union[list, tuple], file_type: Type[File]):
        [cls.add_extension(ext, file_type) for ext in extensions]


class Group(Item):

    def __init__(self, file: File):
        Item.__init__(self)
        self.file = file

        self.groups: List[Group] = []
        self.datasets: List[Dataset] = []


class Dataset(Item):

    def __init__(self, file: File):
        Item.__init__(self)
        self.file = file

        self._shape: Tuple[int] = None
        self._maxshape: Tuple[Union[int,None]] = None
        self._dtype: type = None
        self._data: np.ndarray = None
        self.additional_data = {}

    @property
    def shape(self) -> Tuple[int]:
        return self._shape

    @shape.setter
    def shape(self, shape):
        self._shape = shape

    @property
    def maxshape(self) -> Tuple[int]:
        return self._maxshape

    @maxshape.setter
    def maxshape(self, maxshape):
        self._maxshape = maxshape

    @property
    def dtype(self) -> type:
        return self._dtype

    @dtype.setter
    def dtype(self, dtype):
        self._dtype = dtype

    @property
    def data(self):
        return self._data




class Attribute(ABC):

    def __init__(self, file: File, **kwargs):
        self.file = file

        self._name: str = kwargs.get('name')
        self._shape: Tuple[int] = kwargs.get('shape')
        self._maxshape: Tuple[Union[int,None]] = kwargs.get('maxshape')
        self._dtype: type = kwargs.get('dtype')
        self._data: Any = kwargs.get('data')

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def shape(self) -> Tuple[int]:
        return self._shape

    @shape.setter
    def shape(self, shape):
        self._shape = shape

    @property
    def dtype(self) -> type:
        return self._dtype

    @dtype.setter
    def dtype(self, dtype):
        self._dtype = dtype

    @property
    def data(self) -> Any:
        return self._data

    @data.setter
    def data(self, dtype):
        self._data = dtype


if __name__ == '__main__':
    f1 = File('../sample/h5ex_d_rdwr.h5')
    f2 = File('../sample/h5ex_d_rdwr.h51')