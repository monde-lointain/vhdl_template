# ## Importing modules
from pathlib import Path
import sys  # noqa: E402


# Figure 3: Importing needed resources
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
import random

# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
parent_path = Path("..").resolve()
sys.path.insert(0, str(parent_path))

# ### The tinyalu_utils module

from tinyalu_utils import TinyAluBfm, Ops, alu_prediction, logger


class BaseTester:
    async def execute(self):
        self.bfm = TinyAluBfm()
        ops = list(Ops)
        for op in ops:
            aa, bb = self.get_operands()
            await self.bfm.send_op(aa, bb, op)
        # Send two dummy operations to allow last real operation to complete
        await self.bfm.send_op(0, 0, 1)
        await self.bfm.send_op(0, 0, 1)


class RandomTester(BaseTester):
    def get_operands(self):
        return random.randint(0, 255), random.randint(0, 255)


class MaxTester(BaseTester):
    def get_operands(self):
        return 0xFF, 0xFF


class Scoreboard:
    """
    Provides functionality for gathering data from the DUT, predicting results
    and comparing actual results to predicted results.
    """

    def __init__(self):
        self.bfm = TinyAluBfm()
        self.cmds = []
        self.results = []
        self.cvg = set()

    async def get_cmd(self):
        while True:
            cmd = await self.bfm.get_cmd()
            self.cmds.append(cmd)

    async def get_result(self):
        while True:
            result = await self.bfm.get_result()
            self.results.append(result)

    def start_tasks(self):
        """Begins the data-gathering tasks for the scoreboard"""
        cocotb.start_soon(self.get_cmd())
        cocotb.start_soon(self.get_result())

    def check_results(self):
        """
        Checks each result collected by the scorebard, compares each result
        to the predicted result, and prints the output of the comparison.
        """
        passed = True
        for cmd in self.cmds:
            aa, bb, op_int = cmd
            op = Ops(op_int)
            self.cvg.add(op)
            actual = self.results.pop(0)
            prediction = alu_prediction(aa, bb, op)
            if actual == prediction:
                logger.info(f"PASSED: {aa:02x} {op.name} {bb:02x} = {actual:04x}")
            else:
                logger.error(
                    f"FAILED: {aa:02x} {op.name} {bb:02x} = {actual:04x} - expected {prediction:04x}"
                )
                passed = False

        if len(set(Ops) - self.cvg) > 0:
            logger.error(f"Functional coverage error. Missed: {set(Ops) - self.cvg}")
            passed = False
        else:
            logger.info("Covered all operations")

        return passed


async def execute_test(tester_class):
    """Runs a test case"""
    # Initialize the test environment
    bfm = TinyAluBfm()
    scoreboard = Scoreboard()
    await bfm.reset()
    bfm.start_tasks()
    scoreboard.start_tasks()
    # Execute the tester
    tester = tester_class()
    await tester.execute()
    passed = scoreboard.check_results()
    return passed


@cocotb.test()
async def random_test(dut):
    """Tests random operands"""
    passed = await execute_test(RandomTester)
    assert passed


@cocotb.test()
async def max_test(dut):
    """Tests maximum operands"""
    passed = await execute_test(MaxTester)
    assert passed
