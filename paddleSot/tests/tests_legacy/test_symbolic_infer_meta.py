import unittest

from test_case_base import TestCaseBase

import paddle
from sot import symbolic_translate


def case1(x):
    y = 2 + x
    y = y + 1
    ret = paddle.nn.functional.relu(y)

    assert list(y.meta.shape) == [2]
    z = paddle.concat([x, y])
    assert list(z.meta.shape) == [4]


class TestIf(TestCaseBase):
    def test_if_1(self):
        x = paddle.to_tensor([1.0, 2.0])
        symbolic_translate(case1)(x)


if __name__ == "__main__":
    unittest.main()
