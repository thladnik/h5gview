import sys
import logging
import os

log = logging.getLogger(__name__)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('h5gview usage information')
        print(16 * '-')
        print('Use "open file1 file2 file3 ..."')
        quit()

    command = sys.argv[1]

    logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

    if command == 'open':

        from h5gview.core import FileFactory
        from h5gview.h5 import H5File
        FileFactory.add_extensions(['h5', 'hdf5'], H5File)

        log.info('Open UI application')

        from PySide6 import QtWidgets
        from h5gview import ui


        # Create app and window
        app = QtWidgets.QApplication([])
        main = ui.Main()

        if len(sys.argv) > 2:
            filelist = sys.argv[2:]
            main.open_files(*filelist)

        # Show and run
        sys.exit(app.exec())

    elif command == 'plot2d':

        from h5gview.core import FileGroup
        filelist = sys.argv[2:]
        fg = FileGroup(filelist=filelist)
        tree = fg.get_tree()
        pass
