from md import MD


def main():
    app = MD()
    app.run()
    return app.return_code


if __name__ == "__main__":
    main()
