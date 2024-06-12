# Local Development Instructions

To install the `ethstaker-deposit-cli`, follow these steps:

## Prerequisites

Ensure you have the following software installed on your system:

- **Git**: Version control system to clone the repository. [Download Git](https://git-scm.com/downloads)
- **Python 3.9+**: The programming language required to run the tool. [Download Python](https://www.python.org/downloads/)
- **pip**: Package installer for Python, which is included with Python 3.9+.


## Local Development Steps

1. **Clone the Repository**

    ```sh
    git clone https://github.com/eth-educators/ethstaker-deposit-cli.git
    ```

2. **Navigate to the Project Directory**

    ```sh
    cd ethstaker-deposit-cli
    ```

3. **Install Dependencies**

    ```sh
    pip3 install -r requirements.txt
    ```

4. **Run the CLI**

    You can now run the CLI tool using the following command:

    ```sh
    python3 -m ethstaker_deposit [OPTIONS] COMMAND [ARGS]
    ```

**To execute tests, you will need to install the test dependencies**:
```sh
python3 -m pip install -r requirements_test.txt
python3 -m pytest tests
```
