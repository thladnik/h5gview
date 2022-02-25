import sys
import logging
import os

import h5gview

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

        h5gview.open_ui(sys.argv[2:])

    elif command == 'plot2d':

        from h5gview.core import FileGroup
        filelist = sys.argv[2:]
        fg = FileGroup(filelist=filelist)
        tree = fg.get_tree()
        pass
