"""Wrapper de compatibilidade para a aplicação desktop."""

from desktop_app.main_window import MainWindow, main

__all__ = ["MainWindow", "main"]


if __name__ == "__main__":
    main()
