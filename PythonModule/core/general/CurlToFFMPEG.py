import sys
import shlex
import subprocess


SKIP_HEADERS = {
    "accept-encoding",
    "connection",
    "sec-fetch-dest",
    "sec-fetch-mode",
    "sec-fetch-site",
}

def _build_ffmpeg_command_linux(
    url: str,
    headers: dict,
    output: str = "output.mp4"
) -> str:

    user_agent = None
    referer = None
    normal_headers = []

    for lower_name, (name, value) in headers.items():
        if lower_name in SKIP_HEADERS:
            continue

        if lower_name == "user-agent":
            user_agent = value
            continue

        if lower_name == "referer":
            referer = value
            continue

        normal_headers.append(f"{name}: {value}")

    header_text = ""
    if normal_headers:
        header_text = "\\r\\n".join(normal_headers) + "\\r\\n"

    lines = ["ffmpeg \\"]

    if user_agent:
        lines.append(
            f"  -user_agent {shlex.quote(user_agent)} \\"
        )

    if referer:
        lines.append(
            f"  -referer {shlex.quote(referer)} \\"
        )

    if header_text:
        lines.append(
            f"  -headers {_bash_ansi_c_quote(header_text)} \\"
        )

    lines.append(f"  -i {shlex.quote(url)} \\")
    lines.append("  -c copy \\")
    lines.append(f"  {shlex.quote(output)}")

    return "\n".join(lines)


def _windows_quote(value: str) -> str:
    return subprocess.list2cmdline([value])

def _bash_ansi_c_quote(value: str) -> str:
   
    value = value.replace("\\", "\\\\")
    value = value.replace("'", "\\'")
    return "$'" + value + "'"


def _parseCurl(curl_command: str):
    tokens = shlex.split(curl_command, posix=True)

    if not tokens or tokens[0] != "curl":
        raise ValueError("_parseCurl: Command must start with 'curl'")

    url = None
    headers = {}

    i = 1
    while i < len(tokens):
        token = tokens[i]

        if token in ("-H", "--header"):
            if i + 1 >= len(tokens):
                raise ValueError("_parseCurl: Header without value was found")

            header = tokens[i + 1]

            if ":" in header:
                name, value = header.split(":", 1)
                headers[name.strip().lower()] = (name.strip(), value.strip())

            i += 2
            continue

        if token.startswith("http://") or token.startswith("https://"):
            url = token
            i += 1
            continue

        i += 1

    if not url:
        raise ValueError("_parseCurl: No url was found in curl command")

    return url, headers


def _build_ffmpeg_command_windows(
    url: str,
    headers: dict,
    output: str = "output.mp4"
) -> str:

    user_agent = None
    referer = None
    normal_headers = []

    for lower_name, (name, value) in headers.items():
        if lower_name in SKIP_HEADERS:
            continue

        if lower_name == "user-agent":
            user_agent = value
            continue

        if lower_name == "referer":
            referer = value
            continue

        normal_headers.append(f"{name}: {value}")

    command = ["ffmpeg"]

    if user_agent:
        command.extend([
            "-user_agent",
            user_agent
        ])

    if referer:
        command.extend([
            "-referer",
            referer
        ])

    if normal_headers:
        # Hier absichtlich escaped statt echter Zeilenumbrüche
        header_text = "\\r\\n".join(normal_headers) + "\\r\\n"

        command.extend([
            "-headers",
            header_text
        ])

    command.extend([
        "-i",
        url,
        "-c",
        "copy",
        output
    ])

    return subprocess.list2cmdline(command)


def _build_ffmpeg_command(
    url: str,
    headers: dict,
    output: str = "output.mp4"
) -> str:

    if sys.platform == "win32":
        return _build_ffmpeg_command_windows(
            url,
            headers,
            output
        )

    return _build_ffmpeg_command_linux(
        url,
        headers,
        output
    )



def get_curlToFFmpeg(
    curl_command: str,
    output: str = "output.mp4"
) -> str:

    if not curl_command or not isinstance(curl_command, str):
        raise ValueError(
            "get_curlToFFmpeg: Empty command given "
            "or it wasn't a string"
        )

    url, headers = _parseCurl(curl_command.strip())

    return _build_ffmpeg_command(
        url,
        headers,
        output
    )