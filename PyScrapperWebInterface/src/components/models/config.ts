export const MEDIATYPES = {
    youtube : ["mp3", "mp4"],
    archive : ["mp3", "mp4", "wav", "mkv"],
    bandcamp : ["mp3"]
} as const

export type Provider = keyof typeof MEDIATYPES

export const providers = Object.keys(MEDIATYPES) as Provider[]