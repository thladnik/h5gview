import logging
import sys
from typing import List
from PySide6 import QtWidgets

from h5gview import ui
from h5gview.core import FileFactory
from h5gview.h5 import H5File

FileFactory.add_extensions(['h5', 'hdf5'], H5File)

log = logging.getLogger(__name__)


def open_ui(file_list: List[str]):

    log.info('Open UI application')

    # Get open instance
    app = QtWidgets.QApplication.instance()

    # If no instance available, create new
    if app is None:
        app = QtWidgets.QApplication([])
        external_eventloop = False
    else:
        external_eventloop = True

    main = ui.Main()
    main.open_files(*file_list)

    # Run
    if not external_eventloop:
        print('Run eventloop')
        sys.exit(app.exec())

    return main
