# Reference Image Selector

A production-ready human-in-the-loop image reference selection system for e-commerce catalogs.

## Features

- ✅ Simple navigation (Previous/Next)
- ✅ Multi-user friendly (prevents duplicate work)
- ✅ Resume-safe (tracks completion)
- ✅ Download selections as ZIP
- ✅ Jump to any product
- ✅ Optional color tagging

## Quick Start

### Local Installation

```bash
pip install -r requirements.txt
streamlit run reference_image_selector.py
```

### Web Deployment

1. Fork this repository
2. Add your product images to `output/` folder
3. Deploy on [Streamlit Cloud](https://share.streamlit.io)
4. Share URL with team
5. Download ZIP periodically to retrieve selections

## Usage

1. Enter your name
2. Browse product images
3. Select reference images (check boxes)
4. Optionally assign colors
5. Click "Save & Next"
6. Download completed work via ZIP button

## Structure

```
reference-image-selector/
├── reference_image_selector.py  # Main application
├── requirements.txt             # Python dependencies
├── output/                      # Product images (READ-ONLY)
│   ├── Product_A/
│   │   ├── image_1.jpg
│   │   └── image_2.webp
│   └── Product_B/
└── selected_reference_images/   # Output (auto-generated)
    ├── Product_A/
    │   ├── ref_1_black.jpg
    │   ├── ref_2_unknown.webp
    │   └── selection.json
    └── Product_B/
```

## Multi-User Coordination

The app prevents duplicate work by creating `selection.json` for completed products. All team members see the same completion status.

## License

MIT
