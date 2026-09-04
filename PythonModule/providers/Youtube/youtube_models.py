from enum import Enum

class GetMediaMethod(Enum):
    VISION = "visionos"
    ANDROID_AR = "android_ar"




VISIONOS_CONTEXT = {
    "client": {
        "clientName": "VISIONOS",
        "clientVersion": "1.02",
        "deviceMake": "Apple",
        "deviceModel": "RealityDevice17,1",
        "userAgent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_7_3) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/26.0 Safari/605.1.15"
        ),
        "osName": "visionOS",
        "osVersion": "26.5.23O471",
        "hl": "en",
    }
}


VISIONOS_HEADERS = {
        "Content-Type": "application/json",
        "Origin": "https://www.youtube.com",

        "X-YouTube-Client-Name": "101",
        "X-YouTube-Client-Version": "1.02",

        "User-Agent": VISIONOS_CONTEXT["client"]["userAgent"],
    }




HEADER_MAPPING = {
    GetMediaMethod.VISION : VISIONOS_HEADERS
}

CONTEXT_MAPPING = {
    GetMediaMethod.VISION : VISIONOS_CONTEXT
}