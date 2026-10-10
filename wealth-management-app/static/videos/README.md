# Demo Video Instructions

## How to Add Your Demo Video

1. **Record your demo video** with audio narration explaining your app features
   - Recommended format: MP4
   - Recommended resolution: 1920x1080 (Full HD)
   - Recommended codec: H.264
   - Include audio narration explaining features

2. **Save the video file** in this directory (`static/videos/`)
   - Name it: `app-demo.mp4` (or update the filename in `templates/home.html`)

3. **Update the video path** in `templates/home.html`:
   - Find the `videoConfig` object in the JavaScript
   - Update `localVideo: '/static/videos/app-demo.mp4'` with your filename

## Alternative: Use YouTube or Vimeo

If you prefer to host your video on YouTube or Vimeo:

1. Upload your video to YouTube or Vimeo
2. Get the embed URL:
   - YouTube: `https://www.youtube.com/embed/VIDEO_ID`
   - Vimeo: `https://player.vimeo.com/video/VIDEO_ID`
3. Update `templates/home.html`:
   - Set `youtubeUrl` or `vimeoUrl` in the `videoConfig` object

## Video Content Suggestions

Your demo video should include:
- Introduction to the app
- Portfolio management features
- Retirement planning calculator
- Asset and liability tracking
- Multi-currency support
- How to get started

Keep it concise (2-5 minutes recommended) and focus on key features.
