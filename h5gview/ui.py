from typing import List, Union, Dict
from PySide6 import QtCore, QtGui, QtWidgets
import logging

from h5gview import core
from h5gview import plotting

log = logging.getLogger(__name__)


class Main(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.tree_items = []
        log.info('Open main window')

        geo = self.screen().geometry()
        self.resize(geo.width() // 2, 7 * geo.height() // 10)
        self.setLayout(QtWidgets.QHBoxLayout())

        self._central_widget = QtWidgets.QWidget()
        self._central_widget.setLayout(QtWidgets.QGridLayout())
        self.layout().addWidget(self._central_widget)

        # File tree
        self._file_tree = FileTree(self)
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

    def _mouse_press(self, event: QtGui.QMouseEvent):
        print(event.button())

    def _update_info(self, selected: QtCore.QItemSelection, unselected: QtCore.QItemSelection):
        # Fetch item data
        indices = selected.indexes()
        if len(indices) == 0:
            return

        tree_item = self._file_tree.itemFromIndex(indices[0])
        data_item = tree_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

        log.debug(f'Selected {data_item}')

        # Update info areas
        self._object_info.update_info(data_item)
        self._attribute_info.update_info(data_item)

    def _new_tree_item(self, tree_item: QtWidgets.QTreeWidgetItem, data_item: Union[core.Dataset, core.Group]):
        log.debug(f'Add {data_item} to tree as part of {tree_item.data(0, QtCore.Qt.ItemDataRole.UserRole)}')

        # Create new tree item
        new_item = QtWidgets.QTreeWidgetItem(tree_item)
        new_item.setText(0, data_item.name)
        new_item.setData(0, QtCore.Qt.ItemDataRole.ToolTipRole, str(data_item))
        new_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, data_item)

        # Add to item list
        self.tree_items.append(new_item)

        return new_item

    def _add_group_to_tree(self, tree_item: QtWidgets.QTreeWidgetItem, data: core.Group):

        for group in data.groups:
            new_item = self._new_tree_item(tree_item, group)
            self._add_group_to_tree(new_item, group)

        for dataset in data.datasets:
            self._new_tree_item(tree_item, dataset)

    def update_file_tree(self):
        self._file_tree.clear()
        self.filegroup_tree_items = []

        # Add FileGroups
        for fg in core.FileGroup.filegroup_register:
            tl_item = QtWidgets.QTreeWidgetItem(self._file_tree)
            tl_item.setText(0, str(fg))
            self.filegroup_tree_items.append(tl_item)

            # Add files
            for _, file in fg.files.items():
                file_item = QtWidgets.QTreeWidgetItem(tl_item)
                file_item.setText(0, file.name)
                file_item.setData(0, QtCore.Qt.ItemDataRole.ToolTipRole, str(file.path))
                file_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, file)
                self._add_group_to_tree(file_item, file.get())

            # Expand FileGroup by default
            tl_item.setExpanded(True)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:

        # Clear filegroup register (important if called multiple times within one session)
        core.FileGroup.filegroup_register.clear()

        event.accept()


class FileTree(QtWidgets.QTreeWidget):

    def __init__(self, parent):
        QtWidgets.QTreeWidget.__init__(self, parent=parent)

        self.setColumnCount(1)
        self.itemChanged.connect(self._resize_columns)
        self.itemCollapsed.connect(self._resize_columns)
        self.itemExpanded.connect(self._resize_columns)
        self.setHeaderLabels(['Files'])

        self.click_position = None
        self.plots = {}

    def _resize_columns(self):
        self.resizeColumnToContents(0)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        QtWidgets.QTreeWidget.mousePressEvent(self, event)

        if event.button() is QtCore.Qt.MouseButton.RightButton:
            tree_item = self.itemAt(event.pos())
            data_item = tree_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if data_item is not None:
                self.click_position = event.pos()
                self._open_context_menu_on_item(data_item)

    def _open_context_menu_on_item(self, data_item: Union[core.Dataset, core.Group, core.File]):
        if isinstance(data_item, core.Dataset):
            self._open_dataset_context_menu(data_item)

    def _open_dataset_context_menu(self, data_item: core.Dataset):

        self.context_menu = QtWidgets.QMenu(self)
        for opt in plotting.options(data_item):
            self.context_menu.addAction(f"Plot {opt.__name__}", self._plot(opt, data_item))

        self.context_menu.addSeparator()

        if self.click_position:
            pdiff = QtCore.QPoint(0, self.context_menu.sizeHint().height()//2)
            res = self.click_position+pdiff
            self.context_menu.exec_(self.mapToGlobal(res))
        self.click_position = None

    def _plot(self, plot_type: type, data_item: core.Dataset):
        def _plot():
            log.debug(f'{plot_type.__name__} for {data_item}')
            plot = plot_type(self, data_item)
            self.plots[plot.id] = plot

        return _plot


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
        self.table.setHorizontalHeaderLabels(['Name', 'Data', 'Data type', 'Shape'])

        if data_item is None:
            return

        self.table.setRowCount(len(data_item.attributes))
        for i, attr in enumerate(data_item.attributes):
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(attr.name))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(attr.data)))
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(attr.dtype)))
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(attr.shape)))


class ObjectInfo(QtWidgets.QScrollArea):

    available_fields = dict(name='Name',
                            path='Path',
                            id='Object ID',
                            dtype='Datatype',
                            shape='Shape',
                            maxshape='Maxshape')

    show_for_group = ('name', 'path', 'object_ref')
    show_for_file = ('name', 'path', 'object_ref')
    all_fields = []

    def __init__(self, parent):
        QtWidgets.QScrollArea.__init__(self, parent=parent)
        self.setLayout(QtWidgets.QVBoxLayout())

        self.layout().addWidget(QtWidgets.QLabel('General object information'))

        self.all_fields: Dict[str, ObjectInfoField] = {}
        for name, label in self.available_fields.items():
            self.all_fields[name] = ObjectInfoField(self, label)
            self.layout().addWidget(self.all_fields[name])
        self.data_table = QtWidgets.QTableWidget()
        self.data_table.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        self.layout().addWidget(self.data_table)

    def _new_info_field(self, name):
        # Create field for name
        field = ObjectInfoField(self, name)

        # Add field to layout
        self.layout().addWidget(field)

        return field

    def update_info(self, data_item: Union[core.Dataset, core.Group]):

        # Update fields
        for name, field in self.all_fields.items():
            if data_item is None:
                field.hide()
                continue

            if isinstance(data_item, core.Group) and name not in self.show_for_group:
                field.hide()
            elif isinstance(data_item, core.File) and name not in self.show_for_file:
                field.hide()
            else:
                field.line_edit.setText(str(getattr(data_item, name)))
                field.show()

        # Update data table
        self.data_table.clear()
        if not isinstance(data_item, core.Dataset):
            return

        if len(data_item.shape) == 1:
            self.data_table.setColumnCount(data_item.shape[0])
            self.data_table.setHorizontalHeaderLabels(range(data_item.shape[0]))
            self.data_table.setRowCount(1)

            for i, d in enumerate(data_item.data):
                self.data_table.setItem(0, i, QtWidgets.QTableWidgetItem(d))

        elif len(data_item.shape) == 2:
            self.data_table.setColumnCount(data_item.shape[0])
            self.data_table.setHorizontalHeaderLabels([str(i) for i in range(data_item.shape[0])])
            self.data_table.setRowCount(data_item.shape[1])
            self.data_table.setVerticalHeaderLabels([str(i) for i in range(data_item.shape[1])])

            for i in range(data_item.shape[0]):
                for j in range(data_item.shape[1]):
                    self.data_table.setItem(j, i, QtWidgets.QTableWidgetItem(str(data_item.data[i, j])))


class ObjectInfoField(QtWidgets.QWidget):

    def __init__(self, parent, name):
        QtWidgets.QWidget.__init__(self, parent=parent)

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.label = QtWidgets.QLabel(name)
        self.label.setFixedWidth(120)
        self.layout().addWidget(self.label)
        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setDisabled(True)
        self.layout().addWidget(self.line_edit)


if __name__ == '__main__':
    pass
