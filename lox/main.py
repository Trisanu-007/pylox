import argparse
import sys
from Scanner import Scanner
from TokenType import TokenType
from Lox import Lox


if __name__ == "__main__":

    if len(sys.argv) > 2:
        print("Usage: jlox [script]")
        exit(64)
    elif len(sys.argv) == 2:
        Lox.run_file(filename=sys.argv[1])
    else:
        Lox.run_prompt()
