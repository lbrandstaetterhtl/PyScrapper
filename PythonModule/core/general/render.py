import threading

_print_lock = threading.Lock()

_progress_lines: dict[str, str] = {}
_rendered_lines = 0

#KI Written cause me too dumb
def renderProgress(job_id: str, text: str):
    global _rendered_lines

    with _print_lock:
        _progress_lines[job_id] = text


        if _rendered_lines > 0:
            print(
                f"\033[{_rendered_lines}A",
                end=""
            )

        lines = list(_progress_lines.values())

        for line in lines:

            print(
                f"\r\033[2K{line}"
            )


        for _ in range(_rendered_lines - len(lines)):
            print("\r\033[2K")

        _rendered_lines = len(lines)


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