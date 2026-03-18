import urllib.error, urllib.request
import time

class ArgumentError(Exception): ...

def get_html(
        session = None,
        url: str = None,
        decode: str = "utf-8",
        chunk_size = 8096

)-> str:
    
    if not url:
        raise ArgumentError("No URL was given")
    if not session:
        raise ArgumentError("No Session was given")
    
    request = urllib.request.Request(
        url,
        method="GET",
    )


    try:
        with session.open(request) as response:
            chunks = []
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
            
#the b"" for the join is used so we can python it is Bytes we are dealing with            
            html = b"".join(chunks).decode(decode)
            return html

    except urllib.error.HTTPError as e:
        raise
    
    except urllib.error.URLError as e:
        raise
    
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"Failed to decode with given decode standard {decode}")





def download_to_file(
        request,
        session,
        out_file:str,
        progress_dict: dict,
        chunk_size: int = 8192,
        
        
):
    try:
        with session.open(request) as response, open(out_file, "wb") as f:
            downloading = True

            progress_dict['status'] = "downloading..."

            total_size = int(response.headers.get("Content-Length", 0))
            progress_dict["totalBytes"] = total_size

            downloaded: int = 0
            start_time = time.time()

            while downloading:
                chunk = response.read(chunk_size)
                if not chunk:
                    downloading=False
                    break

                
                f.write(chunk)


                downloaded += len(chunk)
                percent = 100 / total_size * downloaded
                elapsed_time = time.time() - start_time
                


                progress_dict['downloadProgress'] = percent
                progress_dict['downloadedBytes'] = downloaded

                speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                if speed:
                    progress_dict["speed"] = round(speed / 1024 / 1024, 2)
                remaining = total_size - downloaded
                if speed > 0:
                    eta = remaining / speed
                    progress_dict['eta'] = round(eta, 1)
                

        progress_dict['status'] = "complete"

    except Exception:
        raise
    
    
