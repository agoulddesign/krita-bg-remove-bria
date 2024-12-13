# Krita Background Remover (BriaAI)

[![Download](https://img.shields.io/github/v/release/agoulddesign/krita-bg-remove-bria?style=for-the-badge&label=Download)](https://github.com/agoulddesign/krita-bg-remove-bria/releases/)

[![Krita Logo](https://raw.githubusercontent.com/agoulddesign/krita-bg-remove-bria/main/misc/krita05.png)](https://krita.org)

### A powerful Krita plugin for fast and automatic background removal using BriaAI's API.

**Now with lightning fast batch mode.**

Say goodbye to massive servers or third-party apps – isolate subjects effortlessly and quickly within Krita!

### Nov. 2024 Announcement! Bria AI has updated their background removal algorithm, which means an automatic upgrade in the quality and accuracy of background removal with this plugin. No need to update. Enjoy!

## Setup Instructions

1. Create a free BriaAI account and obtain an API key at [www.bria.ai](http://www.bria.ai).
   - No credit card required for first three months
   - 1000 free uses per month
   - Affordable rates thereafter (~$0.08 per use, pay as you go)

2. Download the plugin and import it into Krita:
   - Navigate to `Tools -> Scripts -> Import Python plugin from file...`
   - **Note**: Do not extract the files

3. Enable the docker window:
   - Go to `Settings -> Dockers -> Background Remover BriaAI`

4. Paste your BriaAI API key into the designated field.

## Usage

1. Select the layer(s) for background removal. Select **Batch** mode for multiple.
2. Click **Remove Background**. Processing may take a few seconds.
3. New layer(s) with an alpha channel and removed background will be created.

## Important Considerations

### Alpha Channel and Transparency

- Removing the background of a layer that already has an alpha channel (transparency) can result in odd placement of the resulting image.
- To fix this, turn the original layer back on and align it to the original.
- It is recommended to fill in any transparent areas before removing the background.

### Image Dimensions and Boundaries

- Removing the background of images with different dimensions, or images that extend beyond the visible area, may result in unexpected results.
- For best results, ensure all layers are the same size and do not extend past the visible area. Use the `Image -> Trim to Image Size` tool for this.

### Batch Mode Processing

When processing a large number of layers:

- You can set the number of concurrent working processes (threads) to automatic or increase it to speed up the process.
- Be cautious when increasing threads, as it may cause stability issues, especially on older/slower computers.
- The default setting uses the same number of threads as the number of cores in your processor(s).


> **Note**: The removal process works best on images with clear subjects and minimal depth of field. For complex images, you may need to transfer the alpha of the new layer to the original as a transparency mask for further adjustments.

## About

- BriaAI uses licensed material to train their AI models, ensuring no copyright concerns.
- This plugin is not affiliated with BriaAI or Krita.
- Created primarily with AI assistance – optimizations welcome! Feel free to fork or submit pull requests.

## Compatibility

- Tested with Krita 5.2.2, 5.2.3, 5.2.6
- May not be compatible with other versions

## Known Issues & Future Plans

- **Bug**: Currently works with most color spaces, but may cause some color differences with the result image (most notable with CMYK). This is easily fixed if you simply transfer the alpha from the resulting image to the original.
- **Todo**: Maybe handle different size image layers better

---

### Enjoy the power and simplicity of automatic background removal in Krita!
