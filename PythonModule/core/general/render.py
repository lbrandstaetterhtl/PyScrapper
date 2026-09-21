import threading

_print_lock = threading.Lock()


def renderProgress(job_id: str, text: str):
    text = text.replace("\n", " ").replace("\r", " ")

    with _print_lock:
        print(
            f"\r\033[2K{text}",
            end="",
            flush=True
        )


def makeBorder(
    title: str,
    liste: list[str]
) -> str:
    lines = []

    for string in liste:
        lines.extend(string.splitlines())

    maxLength = max(
        len(title),
        *(len(line) for line in lines)
    )

    prettyString = (
        "+ "
        + title.center(maxLength, "-")
        + " +\n"
    )

    for line in lines:
        prettyString += (
            "| "
            + line
            + " " * (maxLength - len(line))
            + " |\n"
        )

    prettyString += (
        "+ "
        + "-" * maxLength
        + " +\n"
    )

    return prettyString