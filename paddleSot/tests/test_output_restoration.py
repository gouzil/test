from __future__ import annotations

import unittest

from test_case_base import TestCaseBase

import paddle


def output_identity(x):
    return x


def output_const():
    return 42


def output_list(x: paddle.Tensor, y: paddle.Tensor, z: int):
    a = x + 1
    b = z + 1
    l = [1, a, b, y]
    return l


def output_dict(x: paddle.Tensor, y: paddle.Tensor, z: int):
    a = x + 1
    b = z + 1
    l = {1: a, b: y}
    return l


def output_dict_const_key(x: paddle.Tensor, y: paddle.Tensor, z: int):
    a = x + 1
    b = z + 1
    l = {1: a, 2: y}
    return l


def output_nest_struct(x: paddle.Tensor, y: paddle.Tensor, z: int):
    a = x + y + z
    b = z + 1
    l = [1 + 1, (z, a), [b]]
    return l


class TestOutputRestoration(TestCaseBase):
    def test_output_identity(self):
        self.assert_results(output_identity, 1)
        self.assert_results(output_identity, 2)
        self.assert_results(output_identity, paddle.to_tensor(1))

    def test_output_const(self):
        self.assert_results(output_const)

    def test_output_list(self):
        a = paddle.to_tensor(1)
        b = paddle.to_tensor(2)

        self.assert_results(output_list, a, b, 3)

    def test_output_dict(self):
        a = paddle.to_tensor(1)
        b = paddle.to_tensor(2)

        self.assert_results(output_dict, a, b, 3)

    def test_output_dict_const_key(self):
        a = paddle.to_tensor(2)
        b = paddle.to_tensor(3)

        self.assert_results(output_dict_const_key, a, b, 4)

    def test_output_nest_struct(self):
        a = paddle.to_tensor(1)
        b = paddle.to_tensor(2)

        self.assert_results(output_nest_struct, a, b, 3)


if __name__ == "__main__":
    unittest.main()
