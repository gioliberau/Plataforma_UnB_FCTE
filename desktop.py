import sys


def main():
    try:
        import tkinter  # noqa: F401
    except ModuleNotFoundError:
        print(
            'O módulo tkinter não está instalado neste Python.\n'
            'No Ubuntu/Debian instale com: sudo apt install python3-tk\n'
            'No Fedora instale com:        sudo dnf install python3-tkinter',
            file=sys.stderr,
        )
        sys.exit(1)

    from desktop.app import main as executar_app
    executar_app()


if __name__ == '__main__':
    main()
