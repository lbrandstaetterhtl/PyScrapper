import os
ROOT_DIR = os.getcwd()
COOKIE_FILE = os.path.join(ROOT_DIR, "cookies.txt")




BROWSER_ACTIONS = {
    "wait" : int,
    "click" : str,
}

PLAY_BUTTON_SELECTORS = [
        # --------------------------------------------------
        # Video.js
        # --------------------------------------------------
        ".vjs-big-play-button",
        ".video-js .vjs-big-play-button",
        "button.vjs-big-play-button",

        # --------------------------------------------------
        # JW Player
        # --------------------------------------------------
        ".jw-icon-playback",
        ".jw-display-icon-container",
        ".jwplayer .jw-display-icon-container",
        ".jwplayer .jw-icon-playback",
        ".jwplayer [aria-label*='play' i]",

        # --------------------------------------------------
        # Plyr
        # --------------------------------------------------
        ".plyr__control--overlaid",
        ".plyr__control[data-plyr='play']",
        "button[data-plyr='play']",
        ".plyr button[aria-label*='play' i]",

        # --------------------------------------------------
        # Shaka Player
        # --------------------------------------------------
        ".shaka-play-button",
        ".shaka-play-button-container button",
        ".shaka-controls-container button[aria-label*='play' i]",

        # --------------------------------------------------
        # YouTube
        # --------------------------------------------------
        ".ytp-large-play-button",
        ".ytp-play-button",
        "button.ytp-large-play-button",
        "button.ytp-play-button",

        # --------------------------------------------------
        # MediaElement.js
        # --------------------------------------------------
        ".mejs__overlay-button",
        ".mejs__play button",
        ".mejs-playpause-button button",

        # --------------------------------------------------
        # Flowplayer
        # --------------------------------------------------
        ".fp-play",
        ".fp-ui .fp-play",
        ".flowplayer .fp-play",

        # --------------------------------------------------
        # Clappr
        # --------------------------------------------------
        ".media-control-center-panel .play-wrapper",
        ".play-wrapper",
        "[data-playpause]",
        ".container[data-container] .play-wrapper",

        # --------------------------------------------------
        # Bitmovin
        # --------------------------------------------------
        ".bmpui-ui-hugeplaybacktogglebutton",
        ".bmpui-ui-playbacktogglebutton",
        "button[class*='playbacktogglebutton' i]",

        # --------------------------------------------------
        # THEOplayer
        # --------------------------------------------------
        ".theoplayer-play-button",
        ".theoplayer-control-playpause-button",
        "[class*='theoplayer'][class*='play' i]",

        # --------------------------------------------------
        # Kaltura / generic embedded players
        # --------------------------------------------------
        ".largePlayBtn",
        ".playkit-pre-playback-play-button",
        ".playkit-control-button.playkit-playback-button",

        # --------------------------------------------------
        # Odysee / LBRY / generic React players
        # --------------------------------------------------
        "button[data-testid*='play' i]",
        "[data-testid='play-button']",
        "[data-testid='playback-button']",
        "[data-testid*='playback' i]",

        # --------------------------------------------------
        # Generic IDs / classes
        # --------------------------------------------------
        "#play-button",
        "#playButton",
        "#play_button",
        "#playback-button",
        "#playback_button",

        ".play-button",
        ".playButton",
        ".play_button",
        ".playback-button",
        ".playback_button",
        ".big-play-button",
        ".bigPlayButton",

        # Your existing custom names
        "playback_button_svg",
        "playback_button",

        # --------------------------------------------------
        # Accessible buttons
        # --------------------------------------------------
        "button[aria-label='Play']",
        "button[aria-label='play']",
        "button[aria-label*='play' i]",
        "button[aria-label*='resume' i]",
        "button[aria-label*='start' i]",

        "button[aria-label*='abspielen' i]",
        "button[aria-label*='wiedergabe' i]",
        "button[aria-label*='fortsetzen' i]",
        "button[aria-label*='starten' i]",

        # --------------------------------------------------
        # Title attributes
        # --------------------------------------------------
        "button[title='Play']",
        "button[title*='play' i]",
        "button[title*='resume' i]",
        "button[title*='start' i]",

        "button[title*='abspielen' i]",
        "button[title*='wiedergabe' i]",
        "button[title*='starten' i]",

        # --------------------------------------------------
        # role=button elements
        # --------------------------------------------------
        "[role='button'][aria-label*='play' i]",
        "[role='button'][title*='play' i]",
        "[role='button'][aria-label*='abspielen' i]",
        "[role='button'][title*='abspielen' i]",

        # --------------------------------------------------
        # SVG/Icon-based buttons
        # --------------------------------------------------
        "button svg[aria-label*='play' i]",
        "button [class*='play-icon' i]",
        "button [class*='icon-play' i]",
        "[role='button'] [class*='play-icon' i]",

        # --------------------------------------------------
        # Text fallbacks
        # --------------------------------------------------
        "button:has-text('Play')",
        "button:has-text('Abspielen')",
        "button:has-text('Wiedergabe starten')",
        "button:has-text('Video starten')",

        "[role='button']:has-text('Play')",
        "[role='button']:has-text('Abspielen')",

        # --------------------------------------------------
        # Generic class/id contains play
        # Be careful: these are intentionally late
        # --------------------------------------------------
        "button[class*='play' i]",
        "button[id*='play' i]",
        "[role='button'][class*='play' i]",
        "[role='button'][id*='play' i]",

        # --------------------------------------------------
        # Last resort
        # --------------------------------------------------
        "video",
    ]



AD_SKIP_BUTTON_NAMES = [
    # English
    "Skip Ad",
    "Skip Ads",
    "Skip ad",
    "Skip ads",
    "Skip this ad",
    "Skip advertisement",
    "Skip commercial",
    "Skip video",

    # German
    "Werbung überspringen",
    "Anzeige überspringen",
    "Anzeigen überspringen",
    "Werbeanzeige überspringen",

    # Other common variants
    "Skip",
    "Überspringen",
]



COOKIE_ACCEPT_SELECTORS = [
        # Sehr häufig
        "button#onetrust-accept-btn-handler",
        "#onetrust-accept-btn-handler",

        # Sourcepoint
        "button[title='Alle akzeptieren']",
        "button[title='Accept All']",

        # Generische Buttons
        "button:has-text('Alle akzeptieren')",
        "button:has-text('Alles akzeptieren')",
        "button:has-text('Akzeptieren')",
        "button:has-text('Zustimmen')",

        "button:has-text('Accept all')",
        "button:has-text('Accept All')",
        "button:has-text('Accept')",
        "button:has-text('I agree')",
        "button:has-text('Agree')",

        # Häufige aria-label Varianten
        "button[aria-label*='accept' i]",
        "button[aria-label*='akzeptieren' i]",
        "button[aria-label*='zustimmen' i]",

        # Inputs
        "input[type='button'][value*='accept' i]",
        "input[type='submit'][value*='accept' i]",
        "input[type='button'][value*='akzeptieren' i]",
        "input[type='submit'][value*='akzeptieren' i]",
    ]



BAD_MEDIA_KEYWORDS = [
        "ads",
        "banner",
        "promo",
        "tracking",
        "gambling",
        "notification",
        "bonus",
        "click",
        "redirect",
        "jwplayer6",
        "ping.gif",
    ]

GOOD_MEDIA_KEYWORDS = [
    
    "stream",
    "video",
    "media",
    "playlist",
    "master",
    "index",
    "hls",
    "videoplayback",
    "cdn",
    "login",
    
]