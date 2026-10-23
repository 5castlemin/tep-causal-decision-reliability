import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[1]/'scripts/audit_benchmark_compatibility.py'
spec=importlib.util.spec_from_file_location('benchmark_audit',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

TEXT='''Block {
 BlockType Inport
 Name "Temperature"
 Port "9"
}
Block {
 BlockType Constant
 Name "xmv3"
 Value "122.9"
}
Line {
 SrcBlock "xmv3"
 SrcPort 1
 DstBlock "TE Plant"
 DstPort 9
}
'''


class WiringTests(unittest.TestCase):
    def test_name_is_not_manipulated_variable_index(self):
        actual=module.trace_setpoint(TEXT,'Temperature')
        self.assertEqual(actual['port'],9)
        self.assertEqual(actual['constant_block'],'xmv3')
        self.assertEqual(actual['value'],122.9)

    def test_ambiguous_input_rejected(self):
        with self.assertRaises(ValueError):module.trace_setpoint(TEXT+TEXT,'Temperature')

    def test_disconnected_constant_rejected(self):
        with self.assertRaises(ValueError):module.trace_setpoint(TEXT.replace('DstPort 9','DstPort 8'),'Temperature')
