import argparse


def parse_args() -> tuple[str, str, int, bool]:
    """
    Parse command line arguments.

    :return: A list of parsed arguments.
    :rtype: tuple[str, str, int, bool]
    """

    parser = argparse.ArgumentParser(
        prog="LwM2MClient",
        description="LwM2M Client written in Python",
        add_help=True,
    )
    parser.add_argument(
        "--endpoint-name",
        type=str,
        default="lwm2m-client",
        help="Endpoint name",
    )
    parser.add_argument(
        "--server-ip",
        type=str,
        default="leshan.eclipseprojects.io",
        help="Server IP",
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=5684,
        help="Server port",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    args = parser.parse_args()
    return [getattr(args, arg) for arg in vars(args)]
