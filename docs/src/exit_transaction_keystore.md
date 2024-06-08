# exit-transaction-keystore

## Description
Creates an exit transaction using a keystore file.

## Arguments

- **`--chain`**: The chain to use for generating the deposit data. Options are: 'mainnet', 'holesky', etc.

- **`--keystore`**: The keystore file associating with the validator you wish to exit.

- **`--keystore_password`**: The password that is used to encrypt the provided keystore. Note: It's not your mnemonic password.

- **`--validator_index`**: The validator index corresponding to the provided keystore.

- **`--epoch`**: The epoch of when the exit transaction will be valid. The transaction will always be valid by default.

- **`--output_folder`**: The folder path for the `signed_exit_transaction-*` JSON file.


## Example Usage

```sh
./deposit exit-transaction-keystore --keystore /path/to/keystore.json
