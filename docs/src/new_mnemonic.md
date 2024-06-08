# new-mnemonic

## Description
Generates a new BIP-39 mnemonic along with validator keystore and deposit files depending on how many validators you wish to create.

## Arguments

- **`--num_validators`**: Number of validators to create. (Default: 1)

- **`--mnemonic_language`**: The language of the BIP-39 mnemonic. Options are: 'chinese_simplified', 'chinese_traditional', 'czech', 'english', 'french', 'italian', 'japanese', 'korean', 'portuguese', 'spanish'. (Default: 'english')

- **`--chain`**: The chain to use for generating the deposit data. Options are: 'mainnet', 'holesky', etc... (Default: 'mainnet')

- **`--folder`**: The folder where keystore and deposit data files will be saved. (Default: current directory)

- **`--execution_address`**: The Ethereum 1 address for validator withdrawals. (Default: None)

- **`--pbkdf2`**: Will use pbkdf2 key derivation instead of scrypt for generated keystore files as defined in [EIP-2335](https://eips.ethereum.org/EIPS/eip-2335#decryption-key). This can be a good alternative if you intend to work with a large number of keys.

## Example Usage

```sh
./deposit new-mnemonic
