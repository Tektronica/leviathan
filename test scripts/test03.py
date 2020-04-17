from pyunivisa import initialize


def main():
    f5560A, k34461A, f8846A = initialize(3)     # initializes three instruments

    f5560A.info()                               # requests info on instrument
    k34461A.info()
    f8846A.info()


if __name__ == '__main__':
    main()
