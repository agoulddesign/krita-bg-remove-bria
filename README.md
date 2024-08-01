# Krita Background Remover (BriaAI)

[![Download](https://img.shields.io/github/v/release/agoulddesign/krita-bg-remove-bria?style=for-the-badge&label=Download)](https://github.com/agoulddesign/krita-bg-remove-bria/releases/)



![Krita Logo](https://raw.githubusercontent.com/agoulddesign/krita-bg-remove-bria/main/misc/krita03.png)



**A powerful Krita plugin for swift and automatic background removal using BriaAI's API.**

Say goodbye to massive servers or third-party apps – isolate subjects effortlessly within Krita!

## Setup Instructions

1. Create a free BriaAI account and obtain an API key at [www.bria.ai](http://www.bria.ai).
   - No credit card required
   - 1000 free uses per month
   - Affordable rates thereafter (~$0.08 per use)

2. Download the plugin and import it into Krita:
   - Navigate to `Tools -> Scripts -> Import Python plugin from file...`
   - **Note**: Do not extract the files

3. Enable the docker window:
   - Go to `Settings -> Dockers -> Background Remover BriaAI`

4. Paste your BriaAI API key into the designated field.

## Usage

1. Select the layer for background removal.
2. Click **Remove Background** (processing may take a few seconds).
3. A new layer with an alpha channel and removed background will be created.

> **Note**: The removal process works best on images with clear subjects and minimal depth of field. For complex images, you may need to transfer the alpha of the new layer to the original as a transparency mask for further adjustments.

## About

- BriaAI uses ethically trained, licensed material for their AI models, ensuring no copyright or ethical concerns.
- This plugin is not affiliated with BriaAI.
- Created primarily with AI assistance – optimizations welcome! Feel free to fork or submit pull requests.

## Compatibility

- Tested with Krita 5.2.2 and 5.2.3
- May not be compatible with other versions

## Known Issues & Future Plans

- **Bug**: Currently only works in RGBA color space
- **Todo**: Implement batch/multiple mode and optimal layer placement (Coming Soon!)

---

**Enjoy the power and simplicity of automatic background removal in Krita!**
