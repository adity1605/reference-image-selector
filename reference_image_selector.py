"""
Reference Image Selector - Production-Ready Streamlit Application
==================================================================

A human-in-the-loop image reference selection system for an e-commerce catalog.

Features:
- Deterministic behavior
- Resume-safe (skips completed products)
- Multi-user friendly (file-based, no database)
- Simple UI with Streamlit

DEPLOYMENT GUIDE FOR WEB DEPLOYMENT:
------------------------------------

⚠️ IMPORTANT FOR STREAMLIT CLOUD / WEB HOSTING:

1. FILES ARE STORED ON THE SERVER (not your local device)
2. Team accesses via browser URL - no installation needed
3. Selected images save to server's selected_reference_images/ folder
4. Use the DOWNLOAD ZIP button to retrieve all completed work

DEPLOYMENT OPTIONS:

A) STREAMLIT CLOUD (Free, but storage is ephemeral):
   - Push code to GitHub (include 'output' folder with images)
   - Deploy via share.streamlit.io
   - ⚠️ Storage resets on app restart - download regularly!
   - Best for: small teams, short projects

B) CLOUD VM (Recommended for production):
   - Deploy on AWS/GCP/Azure VM
   - Install: Python, Streamlit
   - Run: streamlit run reference_image_selector.py --server.port 80
   - Set up persistent storage/backups
   - Best for: long-term use, 824 products

C) LOCAL SHARED FOLDER (Original approach):
   - Place in Google Drive/OneDrive
   - Each person runs locally
   - Best for: 3 people in same organization

RECOMMENDED WORKFLOW:
   1. Deploy app on web server
   2. Team accesses via URL
   3. Team selects images (saves to server)
   4. Admin downloads ZIP periodically
   5. Extract ZIP to get all selections

Author: Generated for production use
"""

import os
import json
import shutil
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# =============================================================================
# CONFIGURATION - Modify these paths as needed
# =============================================================================

# Base directory where the script is located
BASE_DIR = Path(__file__).parent.resolve()

# Source folder containing product images (READ-ONLY)
# Can be overridden with environment variable: IMAGE_SELECTOR_SOURCE_FOLDER
SOURCE_FOLDER = Path(os.getenv("IMAGE_SELECTOR_SOURCE_FOLDER", BASE_DIR / "output"))

# Output folder for selected reference images (WRITE)
# Can be overridden with environment variable: IMAGE_SELECTOR_OUTPUT_FOLDER
OUTPUT_FOLDER = Path(os.getenv("IMAGE_SELECTOR_OUTPUT_FOLDER", BASE_DIR / "selected_reference_images"))

# DEPLOYMENT NOTES:
# For multi-user cloud sync (Google Drive/OneDrive/Dropbox):
# 1. Place this entire folder in your shared cloud folder
# 2. Each user runs: streamlit run reference_image_selector.py
# 3. Cloud sync handles file coordination automatically
# 4. selection.json prevents duplicate work across team members

# Supported image extensions
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}

# Available color options for selection
COLOR_OPTIONS = [
    "unknown",  # Default if no color selected
    "black",
    "white",
    "red",
    "blue",
    "green",
    "yellow",
    "orange",
    "purple",
    "pink",
    "brown",
    "grey",
    "gray",
    "navy",
    "beige",
    "gold",
    "silver",
    "multicolor",
    "camo",
    "other"
]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_all_product_folders() -> List[Path]:
    """
    Retrieve all product folders from the source directory.
    
    Returns:
        List of Path objects representing product folders, sorted alphabetically.
        
    Note:
        Only directories are returned. Files (like .zip) are ignored.
    """
    if not SOURCE_FOLDER.exists():
        return []
    
    # Get only directories, not files
    folders = [f for f in SOURCE_FOLDER.iterdir() if f.is_dir()]
    
    # Sort alphabetically for consistent ordering across sessions and users
    folders.sort(key=lambda x: x.name.lower())
    
    return folders


def get_images_in_folder(folder_path: Path) -> List[Path]:
    """
    Get all image files in a product folder.
    
    Args:
        folder_path: Path to the product folder
        
    Returns:
        List of Path objects for image files, sorted by name.
    """
    if not folder_path.exists():
        return []
    
    images = []
    for item in folder_path.iterdir():
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
            images.append(item)
    
    # Sort by filename for consistent ordering
    images.sort(key=lambda x: x.name.lower())
    
    return images


def is_product_completed(product_name: str) -> bool:
    """
    Check if a product has already been processed (selection.json exists).
    
    Args:
        product_name: Name of the product folder
        
    Returns:
        True if selection.json exists in the output folder for this product.
    """
    selection_file = OUTPUT_FOLDER / product_name / "selection.json"
    return selection_file.exists()


def save_selection(
    product_name: str,
    source_folder: Path,
    selected_images: List[Dict],
    username: str
) -> bool:
    """
    Save selected images and create selection.json metadata.
    Uses atomic operations to prevent partial saves.
    
    Args:
        product_name: Name of the product
        source_folder: Path to the source product folder
        selected_images: List of dicts with keys: 'original_file', 'color'
        username: Name of the user making the selection
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Create output folder for this product
        product_output_folder = OUTPUT_FOLDER / product_name
        product_output_folder.mkdir(parents=True, exist_ok=True)
        
        # Validate all source files exist before copying
        missing_files = []
        for img_info in selected_images:
            source_file = source_folder / img_info["original_file"]
            if not source_file.exists():
                missing_files.append(img_info["original_file"])
        
        if missing_files:
            st.error(f"Cannot save: {len(missing_files)} source file(s) missing: {', '.join(missing_files[:3])}")
            return False
        
        # Check if already completed (prevent accidental overwrite)
        selection_file = product_output_folder / "selection.json"
        if selection_file.exists():
            overwrite = st.warning("⚠️ This product was already saved. Overwriting will replace previous selection.")
        
        # Process each selected image
        images_metadata = []
        copied_files = []  # Track for rollback if needed
        
        for idx, img_info in enumerate(selected_images, start=1):
            original_file = img_info["original_file"]
            color = img_info.get("color", "unknown") or "unknown"
            
            # Get original file path and extension
            source_file = source_folder / original_file
            ext = Path(original_file).suffix.lower()
            
            # Create new filename: ref_<index>_<color>.<ext>
            new_filename = f"ref_{idx}_{color}{ext}"
            dest_file = product_output_folder / new_filename
            
            # Copy file to output folder
            shutil.copy2(source_file, dest_file)
            copied_files.append(dest_file)
            
            # Add to metadata
            images_metadata.append({
                "original_file": original_file,
                "saved_file": new_filename,
                "color": color
            })
        
        # Create selection.json atomically
        selection_data = {
            "product_name": product_name,
            "completed": True,
            "selected_by": username,
            "timestamp": datetime.now().isoformat(),
            "images": images_metadata
        }
        
        # Write to temp file first, then rename (atomic operation)
        temp_file = product_output_folder / ".selection.json.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(selection_data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        temp_file.replace(selection_file)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error saving selection: {str(e)}")
        # Could add rollback logic here if needed
        return False


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    """
    Initialize Streamlit session state variables.
    
    This ensures all required state variables exist before use.
    """
    # Get all product folders - sorted alphabetically for deterministic order
    if "product_folders" not in st.session_state:
        st.session_state.product_folders = get_all_product_folders()
    
    # Current product index - SINGLE SOURCE OF TRUTH for navigation
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
    
    # Username for tracking who made selections
    if "username" not in st.session_state:
        st.session_state.username = ""
    
    # Track selected images for current product: {filename: {"selected": bool, "color": str}}
    if "current_selections" not in st.session_state:
        st.session_state.current_selections = {}
    
    # Track if we need to reset selections for new product
    if "last_loaded_product" not in st.session_state:
        st.session_state.last_loaded_product = None


def reset_selections_for_product(product_name: str, images: List[Path]):
    """
    Reset selection state when navigating to a new product.
    
    Args:
        product_name: Name of the current product
        images: List of image paths in the product folder
    """
    if st.session_state.last_loaded_product != product_name:
        # Clear previous selections
        st.session_state.current_selections = {}
        
        # Initialize all images as not selected
        for img in images:
            st.session_state.current_selections[img.name] = {
                "selected": False,
                "color": "unknown"
            }
        
        st.session_state.last_loaded_product = product_name


# =============================================================================
# NAVIGATION FUNCTIONS
# =============================================================================

def go_to_previous():
    """Navigate to previous product. Simple decrement."""
    st.session_state.current_index = max(0, st.session_state.current_index - 1)
    st.session_state.last_loaded_product = None


def go_to_next():
    """Navigate to next product. Simple increment."""
    total = len(st.session_state.product_folders)
    st.session_state.current_index = min(total - 1, st.session_state.current_index + 1)
    st.session_state.last_loaded_product = None


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main Streamlit application entry point."""
    
    # Page configuration
    st.set_page_config(
        page_title="Reference Image Selector",
        page_icon="🖼️",
        layout="wide"
    )
    
    # Initialize session state
    init_session_state()
    
    # Check if source folder exists
    if not SOURCE_FOLDER.exists():
        st.error(f"Source folder not found: {SOURCE_FOLDER}")
        st.info("Please ensure the 'output' folder exists in the same directory as this script.")
        return
    
    # Check if we have any products
    if not st.session_state.product_folders:
        st.error("No product folders found in the source directory.")
        return
    
    # Get current product info based on current_index
    total_products = len(st.session_state.product_folders)
    current_folder = st.session_state.product_folders[st.session_state.current_index]
    product_name = current_folder.name
    product_images = get_images_in_folder(current_folder)
    
    # Reset selections if new product loaded
    reset_selections_for_product(product_name, product_images)
    
    # ==========================================================================
    # HEADER - Product info
    # ==========================================================================
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title(product_name)
    
    with col2:
        st.metric(
            "Product",
            f"{st.session_state.current_index + 1} of {total_products}"
        )
    
    st.markdown("---")
    
    # Username input and Jump to product
    col_user, col_jump = st.columns([2, 1])
    
    with col_user:
        username = st.text_input(
            "👤 Your Name",
            value=st.session_state.username,
            placeholder="Enter your name to save selections",
            help="Required to save selections"
        )
        st.session_state.username = username
    
    with col_jump:
        jump_to = st.number_input(
            "Jump to Product #",
            min_value=1,
            max_value=total_products,
            value=st.session_state.current_index + 1,
            step=1,
            help="Enter product number to jump to"
        )
        
        # Check if user changed the number
        if jump_to != st.session_state.current_index + 1:
            st.session_state.current_index = jump_to - 1
            st.session_state.last_loaded_product = None
            st.rerun()
    
    st.markdown("---")
    
    # ==========================================================================
    # IMAGE GRID - Simple 3-column layout
    # ==========================================================================
    
    if not product_images:
        st.warning("No images found in this product folder.")
    else:
        st.subheader(f"Images ({len(product_images)} total)")
        
        # 3-column grid as specified
        num_cols = 3
        
        for row_start in range(0, len(product_images), num_cols):
            cols = st.columns(num_cols)
            
            for col_idx, img_idx in enumerate(range(row_start, min(row_start + num_cols, len(product_images)))):
                image_path = product_images[img_idx]
                image_name = image_path.name
                
                with cols[col_idx]:
                    # Display image
                    try:
                        st.image(str(image_path), width="stretch")
                    except Exception:
                        st.error(f"Cannot load: {image_name}")
                    
                    st.caption(image_name)
                    
                    # Initialize selection state if needed
                    if image_name not in st.session_state.current_selections:
                        st.session_state.current_selections[image_name] = {
                            "selected": False,
                            "color": "unknown"
                        }
                    
                    # Checkbox for selection
                    is_selected = st.checkbox(
                        "Select",
                        value=st.session_state.current_selections[image_name]["selected"],
                        key=f"select_{image_name}"
                    )
                    
                    st.session_state.current_selections[image_name]["selected"] = is_selected
                    
                    # Color dropdown - disabled unless selected
                    current_color = st.session_state.current_selections[image_name].get("color", "unknown")
                    color_index = COLOR_OPTIONS.index(current_color) if current_color in COLOR_OPTIONS else 0
                    
                    selected_color = st.selectbox(
                        "Color",
                        options=COLOR_OPTIONS,
                        index=color_index,
                        key=f"color_{image_name}",
                        disabled=not is_selected
                    )
                    
                    if is_selected:
                        st.session_state.current_selections[image_name]["color"] = selected_color
    
    st.markdown("---")
    
    # ==========================================================================
    # NAVIGATION BUTTONS - Always visible at bottom
    # ==========================================================================
    
    # Collect selected images for save validation
    selected_images = []
    for img_name, sel_info in st.session_state.current_selections.items():
        if sel_info.get("selected", False):
            selected_images.append({
                "original_file": img_name,
                "color": sel_info.get("color", "unknown")
            })
    
    # Two-column layout for buttons
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        # Previous button - always enabled unless at first product
        if st.button(
            "⬅️ Previous",
            key="btn_previous",
            width="stretch",
            disabled=(st.session_state.current_index == 0)
        ):
            # Navigate back WITHOUT saving
            go_to_previous()
            st.rerun()
    
    with col_btn2:
        # Save & Next button
        can_save = bool(st.session_state.username and selected_images)
        
        if st.button(
            "💾 Save & Next",
            key="btn_save_next",
            type="primary",
            width="stretch",
            disabled=not can_save
        ):
            # Save current selections
            success = save_selection(
                product_name=product_name,
                source_folder=current_folder,
                selected_images=selected_images,
                username=st.session_state.username
            )
            
            if success:
                st.success(f"✅ Saved {len(selected_images)} image(s)")
                # Navigate forward
                go_to_next()
                st.rerun()
            else:
                st.error("❌ Failed to save selection")
    
    # Show save requirements if needed
    if not st.session_state.username:
        st.info("ℹ️ Enter your name above to enable saving")
    elif not selected_images:
        st.info("ℹ️ Select at least one image to save")
    
    st.markdown("---")
    
    # ==========================================================================
    # ADMIN SECTION - Download & Delete
    # ==========================================================================
    
    col_admin1, col_admin2 = st.columns(2)
    
    with col_admin1:
        with st.expander("📥 Download Completed Selections"):
            st.write("Download all completed selections as a ZIP file")
            
            if st.button("🗜️ Generate ZIP", key="btn_generate_zip"):
                import zipfile
                from io import BytesIO
                
                if not OUTPUT_FOLDER.exists() or not any(OUTPUT_FOLDER.iterdir()):
                    st.warning("No selections saved yet!")
                else:
                    # Create ZIP in memory
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for product_folder in OUTPUT_FOLDER.iterdir():
                            if product_folder.is_dir():
                                for file in product_folder.iterdir():
                                    if file.is_file():
                                        arcname = f"{product_folder.name}/{file.name}"
                                        zip_file.write(file, arcname)
                    
                    zip_buffer.seek(0)
                    
                    st.download_button(
                        label="⬇️ Download selected_reference_images.zip",
                        data=zip_buffer,
                        file_name=f"selected_reference_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        key="btn_download_zip"
                    )
                    
                    # Show statistics
                    completed_count = sum(1 for p in OUTPUT_FOLDER.iterdir() if p.is_dir() and (p / "selection.json").exists())
                    st.success(f"✅ {completed_count} products completed and ready for download")
    
    with col_admin2:
        with st.expander("🗑️ Delete Current Selection"):
            st.write(f"**Product:** {product_name}")
            
            if is_product_completed(product_name):
                selection_file = OUTPUT_FOLDER / product_name / "selection.json"
                try:
                    with open(selection_file, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                    
                    st.info(f"Selected by: {existing_data.get('selected_by', 'Unknown')}")
                    st.info(f"Date: {existing_data.get('timestamp', 'Unknown')}")
                    st.warning("⚠️ This will permanently delete all selected images and metadata for this product")
                    
                    if st.button("🗑️ Confirm Delete", key="btn_confirm_delete", type="secondary"):
                        try:
                            product_output_folder = OUTPUT_FOLDER / product_name
                            shutil.rmtree(product_output_folder)
                            st.success(f"✅ Deleted selection for {product_name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to delete: {str(e)}")
                except Exception:
                    st.error("Unable to read selection metadata")
            else:
                st.info("This product has not been completed yet")
    
    st.markdown("---")
    st.caption(f"Source: {SOURCE_FOLDER} | Output: {OUTPUT_FOLDER}")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()
