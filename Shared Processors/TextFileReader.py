#!/usr/bin/env python
#
# Copyright 2019 Zack T (mlbz521)
# Borrowed some of the dmg mount logic from included autopkg processors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import os.path
import re

from autopkglib import Processor, ProcessorError
from autopkglib.DmgMounter import DmgMounter

__all__ = ["TextFileReader"]

class TextFileReader(DmgMounter):

    """This process reads a text file and looks for a regex pattern and 
    returns the rest of the line that matched the pattern.  Source path 
    can be a .dmg which will be mounted.
    """

    input_variables = {
        "source": {
            "required": True,
            "description": "Source of the text file.  "
            "Can point to a path inside a .dmg which will be mounted."
        },
        "file_to_open": {
            "required": True,
            "description": "The text file that needs to be opened for reading."
        },
        "pattern": {
            "required": True,
            "description": "The regex pattern to look for and return."
        }
    }
    output_variables = {
        "match": {
            "description": "Returns the rest of the line that matched the pattern."
        }
    }

    description = __doc__

    def main(self):

        # Define variables
        source = os.path.normpath(self.env["source"])
        file_to_open = self.env.get('file_to_open')
        pattern = self.env.get('pattern')

        # Check whether this is at least a valid path
        if not os.path.exists(source):
            raise ProcessorError(f"Path '{source}' doesn't exist!")

        # Check to see if the source is a dmg
        (dmg_path, dmg, dmg_source_path) = self.parsePathForDMG(source)

        self.output(
            f"Parsed dmg results: dmg_path: {dmg_path}, dmg: {dmg}, "
            f"dmg_source_path: {dmg_source_path}",
            verbose_level=2,)

        if dmg:

            try:
                mount_point = self.mount(dmg_path)
                source_path = os.path.join(mount_point, file_to_open)

            except Exception:
                raise ProcessorError("Unable to mount the dmg.")

        else:

            source_path = os.path.join(source, file_to_open)

        # Wrap in a try/finally so if we mount an image, it will always be unmounted.
        try:

            # Open, read, and close file
            file = open(source_path, 'r')
            contents = file.read()
            file.close()

        except Exception:
            raise ProcessorError(f"Unable to open '{file_to_open}'")

        finally:
            if dmg:
                self.unmount(source)

        try:

            # Look for a match
            line = re.search(pattern + r'.*', contents)
            match = re.split(pattern, line.group())[1]

            self.env["match"] = match
            self.output("match: {}".format(self.env["match"]))

        except Exception:
            raise ProcessorError("Unable to find a match based on the pattern provided.")


if __name__ == "__main__":
    processor = TextFileReader()
    processor.execute_shell()
