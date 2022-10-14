from loguru import logger


def read_id() -> int:
    try:
        return int(open("./last_id.txt", "r").read())
    except ValueError:
        logger.critical(
            "The value of the last identifier is incorrect. Please check the contents of the file 'last_id.txt'."
        )
        exit()


def write_id(new_id: int) -> None:
    open("./last_id.txt", "w").write(str(new_id))
    logger.info(f"New ID, written in the file: {new_id}")
