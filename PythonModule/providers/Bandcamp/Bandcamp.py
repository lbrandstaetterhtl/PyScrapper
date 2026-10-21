

# Own imports

from . import models

# Python Default Imports
import urllib.parse



















# def download(
#         download_information: core.models.Download.DownloadInformation,
#         retry = True
# ):
#     core.general.Validate.download.validateDownloadInformation(
#         argument_name="download_information",
#         download_information=download_information,
#         caller="[providers] Bandcamp.download"
#     )
#     core.general.Validate.general.validateBool(boolean=retry, argument_name="retry", caller="[providers] Bandcamp.download")

#     urlType = _validateURL(
#         url=download_information.url
#     )


#     streamingURLList, trackURLList = _extractStreamingURL(
#         url=download_information.url,
#         urlType=urlType,
#         session=download_information.session
#     )


#     for streamingURL, trackURL in zip(streamingURLList, trackURLList):

#         request = urllib.request.Request(
#             streamingURL,
#             method="GET",
#             headers={
#                 "Referer" : streamingURL,
#                 "Origin" : download_information.url,
#                 "Range": "bytes=0-",
#                 }
#             )


#         try:
#             core.download.File.downloadToFile(
#                 request=request,
#                 session=download_information.session,
#                 out_file=download_information.outFile,
#                 progress_dict=download_information.downloadProgress,

#             )
#         except urllib.error.HTTPError as e:
#             if e.code == 403 and retry and urlType !="streamURL":
#                 retry = False

#                 trackHTML = html.getHtml(
#                     url=trackURL,
#                     session=download_information.session
#                 )
#                 core.general.Validate.general.validateStr(argument_name="trackHTML", string=trackHTML, caller="[providers] Bandcamp.download.error")

#                 embeddedplayer_pattern = r'<meta property="og:video".*?content="(https://bandcamp.com/EmbeddedPlayer.*?)">'
#                 embeddedPlayerUrl = core.general.DataSearch.searchBlocks(
#                     pattern=embeddedplayer_pattern,
#                     search_block=trackHTML
#                 )
#                 core.general.Validate.general.validateStr(argument_name="embeddedPlayerUrl", string=embeddedPlayerUrl, caller="[providers] Bandcamp.download.error")

#                 EmergencyBrowser.BrowserButtonPress(url=embeddedPlayerUrl, button_name="#big_play_button")


#                 core.download.File.downloadToFile(
#                     request=request,
#                     session=download_information.session,
#                     out_file=download_information.outFile,
#                     progress_dict=download_information.downloadProgress

#                 )
#             else: raise