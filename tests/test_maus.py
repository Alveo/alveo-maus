import unittest
import os

from maus.maus import *

class MAUSTest(unittest.TestCase):

    def test_bpf(self):
        """We can generate a valid BPF file from a text"""
        bpf_ref = 'ORT: 0 hello\nORT: 1 world\nKAN: 0 h6`l@}\nKAN: 1 w3:ld'

        bpf = build_bpf("hello world")
        self.assertEqual(bpf_ref, bpf)

        bpf = build_bpf("")
        self.assertEqual("\n", bpf)


    def test_call_maus(self):

        bpf = build_bpf("alan")
        textgrid = call_maus("tests/1_1119_2_22_001-ch6-speaker16.wav", bpf, language='aus')

        # check a couple of lines form the output textgrid
        self.assertIn('xmin = 1.010000\n            xmax = 1.120000\n            text = "{"', textgrid)
        self.assertIn('xmin = 1.300000\n            xmax = 1.580000\n            text = "n"', textgrid)
