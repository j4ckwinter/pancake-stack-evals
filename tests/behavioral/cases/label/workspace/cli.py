import sys


def main():
    if sys.argv[1:] == ["--help"]:
        print("Availble commands: status, help")
    else:
        print("ready")


if __name__ == "__main__":
    main()
