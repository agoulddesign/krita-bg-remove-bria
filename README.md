# krita-bg-remove-bria

**A simple plugin for Krita that quickly and automatically removes the background of an image using BriaAI's API.**

No need to load a third party app or website every time you need a subject isolated.

[DOWNLOAD](https://github.com/agoulddesign/krita-bg-remove-bria/releases/)

**Setup instructions:**

  1. You will need a free BriaAI account and API key. As of the writing of this document, it doesn't require a credit card and includes 1000 uses per month and very reasonable prices after that (~ $0.08 per). Go to http://www.bria.ai to sign up.

  2. Download the plugin and import in Krita through "Tools -> Scripts -> Import Python plugin from file..." (note: do not extract the files).

  3. Enable the docker window through "Settings -> Dockers -> Background Remover BriaAI".

  4. Copy your BriaAi API key from the website and paste into the API Key field.

**Usage:**

  1. Select the layer you want to remove the background of and click **Remove Background** (it may take a few seconds). It will then create a new layer with an alpha channel and background removed.
     
  2. The removal process doesn't work very well on images with depth of field or with a lot of subjects/objects in them, or if they're on many different levels (IE foreground, midground, background). If the removal doesn't work quite as expected you can transfer the alpha of the new layer with the background removed to the original layer as a transparency mask and adjust accordingly.

**I hope you enjoy the power and ease of automatic background removal in Krita!**

Please note this plugin was created mostly with the aid of AI, and may not be optimised properly. If you have any ideas on improving it, please feel free to do so!

Created and tested with Krita 5.2.2 and 5.2.3. May not work with other versions.

_I am in no way affiliated with BriaAI._

_Known bug: Only works in RGBA color space_

_Todo: Batch/multiple mode, placing the new layer just above the layer being removed_

