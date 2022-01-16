from powertrip import Powertrip
from powertrip import ModQueueStream


def main():
    pt = Powertrip()
    pt.add_cog(ModQueueStream(pt))
    pt.run()


if __name__ == "__main__":
    main()
