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


@cocotb.test()
async def alu_test(dut):
    """Test all TinyALU operations"""
    passed = True

    # Create a BFM instance
    bfm = TinyAluBfm()
    await bfm.reset()
    bfm.start_tasks()
    cvg = set()

    # Create commands with the constrained random parameters and send them to
    # the ALU
    ops = list(Ops)
    for op in ops:
        aa = random.randint(0, 255)
        bb = random.randint(0, 255)
        await bfm.send_op(aa, bb, op)

        # When the command from the DUT arrives, store it in the coverage set
        seen_cmd = await bfm.get_cmd()
        seen_op = Ops(seen_cmd[2])
        cvg.add(seen_op)

        # Check the result against the predicted value
        result = await bfm.get_result()
        expected = alu_prediction(aa, bb, op)
        if result == expected:
            logger.info(f"PASSED: {aa:02x} {op.name} {bb:02x} = {result:04x}")
        else:
            logger.error(
                f"FAILED: {aa:02x} {op.name} {bb:02x} = {result:04x} - expected {expected:04x}"
            )
            passed = False

    if len(set(Ops) - cvg) > 0:
        logger.error(f"Functional coverage error. Missed: {set(Ops) - cvg}")
        passed = False
    else:
        logger.info("Covered all operations")

    assert passed
