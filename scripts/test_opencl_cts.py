#!/usr/bin/env python3

import unittest
import os
from xml.etree import ElementTree
import subprocess
from functools import partial
import re
import sys

ANDROID_RUNNER_REQUIRED_VERBOSITY = 2
TEST_CONFIG = os.path.join(os.path.dirname(__file__), "test_opencl_cts.xml")


def run_command(command):
  serial_number = os.environ.get("ANDROID_SERIAL", "")
  if not serial_number:
    raise "$ANDROID_SERIAL is empty, device must be specified"
  full_command = ["adb", "-s", serial_number, "shell"] + command
  ret = subprocess.run(
      full_command, capture_output=True, universal_newlines=True)
  return ret.returncode, ret.stdout, ret.stderr


class OpenCLTest(unittest.TestCase):

  def __init__(self, test_name, binary_path, args):
    self._test_name = test_name
    self._binary_path = binary_path
    self._args = args

    self._command = list(map(str.strip, [self._binary_path] + self._args))
    self.test_func_name = f"test_{self._test_name}"

    setattr(self, self.test_func_name, self.genericTest)
    super().__init__(methodName=self.test_func_name)

  def genericTest(self):
    retcode, output, oerror = run_command(self._command)
    self.assertFalse(retcode, "Test exited with non-zero status")

    # TODO(b/158646251): Update upstream to exit with proper error code
    statline_regex = re.compile("^passed \d+ of \d+ tests.")
    passed = total = None
    for line in reversed(output.split("\n")):
      if statline_regex.match(line.strip().lower()):
        _, passed, _, total, *_ = line.strip().split()
        passed = int(passed)
        total = int(total)

    self.assertTrue(passed is not None, "Couldn't find status line")
    self.assertTrue(total is not None, "Couldn't find status line")
    self.assertEqual(passed, total, "{} subtests failed".format(total - passed))


def main():
  """main entrypoint for test runner"""
  _, test_name, binary_path, *args = sys.argv

  suite = unittest.TestSuite()
  suite.addTest(OpenCLTest(test_name, binary_path, args))

  runner = unittest.TextTestRunner(
      stream=sys.stderr, verbosity=ANDROID_RUNNER_REQUIRED_VERBOSITY)
  runner.run(suite)


if __name__ == "__main__":
  main()
