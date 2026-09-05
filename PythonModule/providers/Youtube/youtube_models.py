from enum import Enum

class GetMediaMethod(Enum):
    VISION = "visionos"
    ANDROID_AR = "android_ar"
    SAFARI_WEB = "safari_web"




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


ANDROID_VR_CONTEXT = {
    "client": {
        "clientName": "ANDROID_VR",
        "clientVersion": "1.65.10",

        "deviceMake": "Oculus",
        "deviceModel": "Quest 3",

        "androidSdkVersion": 32,

        "userAgent": (
            "com.google.android.apps.youtube.vr.oculus/1.65.10 "
            "(Linux; U; Android 12L; "
            "eureka-user Build/SQ3A.220605.009.A1) gzip"
        ),

        "osName": "Android",
        "osVersion": "12L",

        "hl": "en",
    }
}


ANDROID_VR_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://www.youtube.com",

    "X-YouTube-Client-Name": "28",
    "X-YouTube-Client-Version": "1.65.10",

    "User-Agent": ANDROID_VR_CONTEXT["client"]["userAgent"],
}

WEB_SAFARI_CONTEXT = {
    "client": {
        "clientName": "WEB",
        "clientVersion": "2.20260708.00.00",

        "userAgent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/15.5 Safari/605.1.15,gzip(gfe)"
        ),

        "hl": "en",
    }
}


WEB_SAFARI_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://www.youtube.com",

    "X-YouTube-Client-Name": "1",
    "X-YouTube-Client-Version": "2.20260708.00.00",

    "User-Agent": WEB_SAFARI_CONTEXT["client"]["userAgent"],
}



HEADER_MAPPING = {
    GetMediaMethod.VISION : VISIONOS_HEADERS,
    GetMediaMethod.ANDROID_AR : ANDROID_VR_HEADERS,
    GetMediaMethod.SAFARI_WEB : WEB_SAFARI_HEADERS

}

CONTEXT_MAPPING = {
    GetMediaMethod.VISION : VISIONOS_CONTEXT,
    GetMediaMethod.ANDROID_AR : ANDROID_VR_CONTEXT,
    GetMediaMethod.SAFARI_WEB : WEB_SAFARI_CONTEXT
}


GET_METHODS = [
    GetMediaMethod.VISION,
    GetMediaMethod.ANDROID_AR,
    GetMediaMethod.SAFARI_WEB
    
]