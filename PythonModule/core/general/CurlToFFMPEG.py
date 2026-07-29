import sys
import shlex


SKIP_HEADERS = {
    "accept-encoding",
    "connection",
    "sec-fetch-dest",
    "sec-fetch-mode",
    "sec-fetch-site",
}


def _shellQuote(value: str) -> str:
    return shlex.quote(value)





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


def _build_ffmpeg_command(url: str, headers: dict, output: str = "output.mp4"):
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
        lines.append(f"  -user_agent {_shellQuote(user_agent)} \\")

    if referer:
        lines.append(f"  -referer {_shellQuote(referer)} \\")

    if header_text:
        lines.append(f"  -headers {_bash_ansi_c_quote(header_text)} \\")

    lines.append(f"  -i {_shellQuote(url)} \\")
    lines.append("  -c copy \\")
    lines.append(f"  {_shellQuote(output)}")

    return "\n".join(lines)


def main():
    print("Paste whole curl command here")
    print("Confirm with 'control + D'\n")


    _curlCommand = sys.stdin.read().strip()


    if not _curlCommand:
        print("No input was given", file=sys.stderr)
        sys.exit(1)


    try:
        url, headers = _parseCurl(_curlCommand)
        _ffmpegCommand = _build_ffmpeg_command(url, headers)
        print("\nAusgabe:\n")
        print(_ffmpegCommand)

    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)






def get_curlToFFmpeg(
    curl_command: str,
    output: str = "output.mp4"
) -> str:
    """
    Takes curl command as string
    Gives back ffmpeg command with curl headers

    """

    if not curl_command or not isinstance(curl_command, str):
        raise ValueError("get_curlToFFmpeg: Empty command given or it wasn't a string")

    url, headers = _parseCurl(curl_command.strip())
    return _build_ffmpeg_command(url, headers, output)



if __name__ == "__main__":
    main()