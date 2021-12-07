from typing import List, Union, Dict
from PySide6 import QtCore, QtWidgets
import logging

from h5gview import core

log = logging.getLogger(__name__)


class Main(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)

        self.tree_items = []
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
        self._object_info = ObjectInfo(self)
        self._central_widget.layout().addWidget(self._object_info, 0, 1)

        # Attribute info
        self._attribute_info = AttributeInfo(self)
        self._central_widget.layout().addWidget(self._attribute_info, 1, 1)
        # Connect for updates
        self._file_tree.selectionModel().selectionChanged.connect(self._update_info)

        self.filegroup_tree_items: List[QtWidgets.QTreeWidgetItem] = []
        self.show()

    def open_files(self, *files: List[Union[str, core.File]], fg: core.FileGroup = None):
        fg_msg = f'for {fg}' if fg is not None else ''
        log.info(f'Open files {files} {fg_msg}')
        if fg is None:
            fg = core.FileGroup()

        for f in files:
            fg.attach_file(f)

        self.update_file_tree()

    def _update_info(self, selected: QtCore.QItemSelection, unselected: QtCore.QItemSelection):
        # Fetch item data
        tree_item = self._file_tree.itemFromIndex(selected.indexes()[0])
        data_item = tree_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

        # Update info areas
        self._object_info.update_info(data_item)
        self._attribute_info.update_info(data_item)


    def _new_tree_item(self, tree_item: QtWidgets.QTreeWidgetItem, data_item: Union[core.Dataset, core.Group]):
        new_item = QtWidgets.QTreeWidgetItem(tree_item)
        new_item.setText(0, data_item.name)
        new_item.setData(0, QtCore.Qt.ItemDataRole.ToolTipRole, str(data_item))
        new_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, data_item)

        self.tree_items.append(new_item)

        return new_item

    def _add_group_to_tree(self, tree_item: QtWidgets.QTreeWidgetItem, data: core.Group):
        for group in data.groups:
            new_item = self._new_tree_item(tree_item, group)
            self._add_group_to_tree(new_item, group)

        for dataset in data.datasets:
            new_item = self._new_tree_item(tree_item, dataset)

    def update_file_tree(self):
        self._file_tree.clear()
        self.filegroup_tree_items = []

        # Add FileGroups
        for fg in core.FileGroup.filegroup_register:
            tl_item = QtWidgets.QTreeWidgetItem(self._file_tree)
            tl_item.setText(0, str(fg))
            self.filegroup_tree_items.append(tl_item)

            # Add files
            for id, file in fg.files.items():
                file_item = QtWidgets.QTreeWidgetItem(tl_item)
                file_item.setText(0, file.name)
                self._add_group_to_tree(file_item, file.get())

            # Expand FileGroup by default
            tl_item.setExpanded(True)

    def _resize_file_tree_columns(self):
        self._file_tree.resizeColumnToContents(0)


class AttributeInfo(QtWidgets.QScrollArea):

    def __init__(self, parent):
        QtWidgets.QScrollArea.__init__(self, parent=parent)
        self.setLayout(QtWidgets.QVBoxLayout())

        self.layout().addWidget(QtWidgets.QLabel('Attached attributes'))

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.layout().addWidget(self.table)

    def update_info(self, data_item: Union[core.Dataset, core.Group]):
        self.table.clear()

        if data_item is None:
            return

        self.table.setRowCount(len(data_item.attributes))
        self.table.setHorizontalHeaderLabels(['Name', 'Data', 'Data type', 'Shape'])
        for i, attr in enumerate(data_item.attributes):
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(attr.name))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(attr.data)))
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(attr.dtype)))
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(attr.shape)))


class ObjectInfo(QtWidgets.QScrollArea):

    def __init__(self, parent):
        QtWidgets.QScrollArea.__init__(self, parent=parent)

        self.setLayout(QtWidgets.QHBoxLayout())
        self.table = QtWidgets.QTableWidget()
        self.layout().addWidget(self.table)

    def update_info(self, data_item: Union[core.Dataset, core.Group]):
        pass
        print(data_item)



if __name__ == '__main__':
    pass