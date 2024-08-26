import pytest
import sys
from typing import (
    Any,
)

from ethstaker_deposit.exceptions import ValidationError
from ethstaker_deposit.settings import get_chain_setting
from ethstaker_deposit.utils.validation import (
    normalize_input_list,
    validate_int_range,
    validate_partial_deposit_amount,
    validate_password_strength,
    validate_signed_exit,
)


@pytest.mark.parametrize(
    'password, valid',
    [
        ('12345678', True),
        ('1234567', False),
    ]
)
def test_validate_password_strength(password: str, valid: bool) -> None:
    if valid:
        validate_password_strength(password=password)
    else:
        with pytest.raises(ValidationError):
            validate_password_strength(password=password)


@pytest.mark.parametrize(
    'password, encoding, platform, valid',
    [
        ('Surströmming', 'utf-8', 'linux', True),
        ('Surströmming', 'latin-1', 'linux', False),
        ('Surstromming', 'latin-1', 'linux', True),
        ('Surströmming', 'utf-8', 'darwin', True),
        ('Surströmming', 'latin-1', 'darwin', False),
        ('Surstromming', 'latin-1', 'darwin', True),
        ('Surströmming', 'utf-8', 'win32', True),
        ('Surströmming', 'latin-1', 'win32', False),
        ('Surstromming', 'latin-1', 'win32', True),
    ]
)
def test_validate_password_strength_encoding(
    monkeypatch, password: str, encoding: str, platform: str, valid: bool
) -> None:
    class MockStdin:
        def __init__(self, encoding):
            self.encoding = encoding
    mock_stdin = MockStdin(encoding=encoding)
    monkeypatch.setattr(sys, 'stdin', mock_stdin)
    monkeypatch.setattr(sys, 'platform', platform)

    if valid:
        validate_password_strength(password=password)
    else:
        with pytest.raises(ValidationError):
            validate_password_strength(password=password)


@pytest.mark.parametrize(
    'num, low, high, valid',
    [
        (2, 0, 4, True),
        (0, 0, 4, True),
        (-1, 0, 4, False),
        (4, 0, 4, False),
        (0.2, 0, 4, False),
        ('0', 0, 4, True),
        ('a', 0, 4, False),
    ]
)
def test_validate_int_range(num: Any, low: int, high: int, valid: bool) -> None:
    if valid:
        validate_int_range(num, low, high)
    else:
        with pytest.raises(ValidationError):
            validate_int_range(num, low, high)


@pytest.mark.parametrize(
    'amount, valid',
    [
        ('-1', False),
        ('0', False),
        ('0.99999', False),
        ('1', True),
        ('1.000000001', True),
        ('1.0000000001', False),
        ('32', True),
        ('18446744073.709551615', True),
        ('18446744073.709551616', False),
        ('18446744073.7095516151', False),
        ('a', False),
        (' ', False)
    ]
)
def test_validate_partial_deposit_amount(amount: str, valid: bool) -> None:
    if valid:
        validate_partial_deposit_amount(amount)
    else:
        with pytest.raises(ValidationError):
            validate_partial_deposit_amount(amount)


@pytest.mark.parametrize(
    'input, result',
    [
        ('1', ['1']),
        ('1,2,3', ['1', '2', '3']),
        ('[1,2,3]', ['1', '2', '3']),
        ('(1,2,3)', ['1', '2', '3']),
        ('{1,2,3}', ['1', '2', '3']),
        ('1 2 3', ['1', '2', '3']),
        ('1  2  3', ['1', '2', '3']),
    ]
)
def test_normalize_input_list(input, result):
    assert normalize_input_list(input) == result


valid_pubkey = "911e7c7fc980bcf5400980917ee92797d52d226768e1b26985fabaf5f214464059ab2d52170b0605f4c8e7a872cde436"
valid_signature = (
    "0x854053a7faebf4547ca3904ff14d896a994d5fb7289478681842fb72622364cd0cb4922170a370ea53234a734b47cd6"
    "80c7edca86e8d796abd8eaeb8dd85d99e57c962c84d6642dff4b6e9bfb6d6df5fa22910c583f13135f5b2b43e4f95e8cf"
)
invalid_pubkey = "b54186e3dbdde180cc39f52e0cf4207c5745a50e2e8bd12f49b925f87682cab88ef108f60cf3ea1ac82b7c6fe796f5d6"
invalid_signature = (
    "0x8cceb99d17361031e01dfb6aa997554a35f60bcc8a106ac76fdea6f5a4780fb8b65b4cd827bca0c88b340508b69f577"
    "50122db94c319aa05a0165e71b41f30c0982c415727b7e2387cce78d995acd54f038b743dc1426b0fb0d4783617d4fe6e"
)


@pytest.mark.parametrize(
    'chain, epoch, validator_index, pubkey, signature, result',
    [
        # valid
        ('mainnet', 0, 0, valid_pubkey, valid_signature, True),
        # bad chain
        ('holesky', 0, 0, valid_pubkey, valid_signature, False),
        # bad epoch
        ('mainnet', 1, 0, valid_pubkey, valid_signature, False),
        # bad validator_index
        ('mainnet', 0, 1, valid_pubkey, valid_signature, False),
        # bad pubkey
        ('mainnet', 0, 0, invalid_pubkey, valid_signature, False),
        # bad signature
        ('mainnet', 0, 0, valid_pubkey, invalid_signature, False),
    ]
)
def test_validate_signed_exit(
    chain: str, epoch: int, validator_index: int, pubkey: str, signature: str, result: bool
) -> None:
    chain_settings = get_chain_setting(chain)

    assert validate_signed_exit(validator_index, epoch, signature, pubkey, chain_settings) == result
