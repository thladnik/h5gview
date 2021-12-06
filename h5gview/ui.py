from typing import List, Union, Dict
from PySide6 import QtCore, QtWidgets
import logging

from h5gview import core

log = logging.getLogger(__name__)


class Main(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)

        self.file_groups: List[core.FileGroup] = []
        log.info('Open main window')

        geo = self.screen().geometry()
        self.move(0, 0)
        self.resize(geo.width() // 2, 9 * geo.height() // 10)

        self._central_widget = QtWidgets.QWidget()
        self._central_widget.setLayout(QtWidgets.QGridLayout())
        self.setCentralWidget(self._central_widget)

        # File tree
        self._file_tree = QtWidgets.QTreeWidget(self)
        self._file_tree.setColumnCount(1)
        self._file_tree.itemChanged.connect(self._resize_file_tree_columns)
        self._file_tree.itemCollapsed.connect(self._resize_file_tree_columns)
        self._file_tree.itemExpanded.connect(self._resize_file_tree_columns)
        self._file_tree.setHeaderLabels(['Files'])
        self._central_widget.layout().addWidget(self._file_tree, 0, 0, 2, 1)

        # Object info
        self._object_info = QtWidgets.QScrollArea(self)
        self._central_widget.layout().addWidget(self._object_info, 0, 1)

        # # Attribute info
        self._attribute_info = QtWidgets.QScrollArea(self)
        self._central_widget.layout().addWidget(self._attribute_info, 1, 1)


        self.toplevel_tree_items = None
        self.show()

    def open_files(self, *files, fg: core.FileGroup = None):
        fg_msg = f'for {fg}' if fg is not None else ''
        log.info(f'Open files {files} {fg_msg}')
        if fg is None:
            fg = core.FileGroup()

        for f in files:
            fg.attach_file(f)

        self.file_groups.append(fg)

        self.update_file_tree()

    def _add_to_tree(self, tree_item, data: Dict[str, Dict[str, Union[core.H5Group, core.H5Dataset]]]):
        for name, item in data.items():
            new_item = QtWidgets.QTreeWidgetItem(tree_item)
            new_item.setText(0, name)
            print(name, item)

            # Follow tree
            if isinstance(item, core.H5Group):
                self._add_to_tree(new_item, item)

    def update_file_tree(self):
        self._file_tree.clear()
        self.toplevel_tree_items = []
        for fg in self.file_groups:
            tl_item = QtWidgets.QTreeWidgetItem(self._file_tree)
            tl_item.setText(0, str(fg))

            for filename, f in fg.get_tree().items():
                file_item = QtWidgets.QTreeWidgetItem(tl_item)
                file_item.setText(0, filename)
                self._add_to_tree(file_item, f)

            # tree = fg.get_tree()
            # import pprint
            #
            # pprint.pprint(tree)



    def _resize_file_tree_columns(self):
        self._file_tree.resizeColumnToContents(0)
        self._file_tree.resizeColumnToContents(1)


if __name__ == '__main__':
    pass