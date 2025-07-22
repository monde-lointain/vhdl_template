# ## Importing modules
from pathlib import Path
import sys  # noqa: E402
import random

import cocotb
import pyuvm
from pyuvm import *

# All testbenches use tinyalu_utils, so store it in a central place and add its
# path to the sys path so we can import it
parent_path = Path("..").resolve()
sys.path.insert(0, str(parent_path))

from tinyalu_utils import TinyAluBfm, Ops, alu_prediction, logger


class BaseTester(uvm_component):
    def start_of_simulation_phase(self):
        self.bfm = TinyAluBfm()

    async def launch_tb(self):
        """Initialize the test case"""
        await self.bfm.reset()
        self.bfm.start_tasks()

    def get_operands(self):
        raise RuntimeError("You must extend BaseTester and override get_operands()")

    async def run_phase(self):
        self.raise_objection()
        await self.launch_tb()
        ops = list(Ops)
        for op in ops:
            aa, bb = self.get_operands()
            await self.bfm.send_op(aa, bb, op)
        # Send two dummy operations to allow last real operation to complete
        await self.bfm.send_op(0, 0, 1)
        await self.bfm.send_op(0, 0, 1)
        self.drop_objection()


class RandomTester(BaseTester):
    def get_operands(self):
        return random.randint(0, 255), random.randint(0, 255)


class MaxTester(BaseTester):
    def get_operands(self):
        return 0xFF, 0xFF


class Scoreboard(uvm_component):
    """
    Provides functionality for gathering data from the DUT, predicting results
    and comparing actual results to predicted results.
    """

    async def get_cmd(self):
        while True:
            cmd = await self.bfm.get_cmd()
            self.cmds.append(cmd)

    async def get_result(self):
        while True:
            result = await self.bfm.get_result()
            self.results.append(result)

    def start_of_simulation_phase(self):
        self.bfm = TinyAluBfm()
        self.cmds = []
        self.results = []
        self.cvg = set()
        cocotb.start_soon(self.get_cmd())
        cocotb.start_soon(self.get_result())

    def check_phase(self):
        passed = True
        for cmd in self.cmds:
            aa, bb, op_int = cmd
            op = Ops(op_int)
            self.cvg.add(op)
            actual = self.results.pop(0)
            prediction = alu_prediction(aa, bb, op)
            if actual == prediction:
                self.logger.info(f"PASSED: {aa:02x} {op.name} {bb:02x} = {actual:04x}")
            else:
                self.logger.error(
                    f"FAILED: {aa:02x} {op.name} {bb:02x} = {actual:04x} - expected {prediction:04x}"
                )
                passed = False

        if len(set(Ops) - self.cvg) > 0:
            self.logger.error(
                f"Functional coverage error. Missed: {set(Ops) - self.cvg}"
            )
            passed = False
        else:
            self.logger.info("Covered all operations")

        assert passed


class AluEnv(uvm_env):
    def build_phase(self):
        self.scoreboard = Scoreboard("scoreboard", self)
        self.tester = BaseTester.create("tester", self)


@pyuvm.test()
class RandomTest(uvm_test):
    """Tests with random operations"""

    def build_phase(self):
        uvm_factory().set_type_override_by_type(BaseTester, RandomTester)
        self.env = AluEnv("env", self)


@pyuvm.test()
class MaxTest(uvm_test):
    """Tests with maximum operands"""

    def build_phase(self):
        uvm_factory().set_type_override_by_type(BaseTester, MaxTester)
        self.env = AluEnv("env", self)
