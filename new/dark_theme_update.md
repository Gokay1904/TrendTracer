# Dark Theme Implementation for Crypto Portfolio Manager

This update adds a modern, visually appealing dark theme to the application with improved UI design and color scheme.

## Changes Made:

1. Created a comprehensive theme system in `app/ui/theme.py` with:
   - Consistent color palette
   - Stylesheet management
   - Helper functions for table styling and color handling

2. Updated the main application to use the dark theme by:
   - Applying stylesheets globally
   - Setting the application palette
   - Using the Fusion style for better dark theme support

3. Enhanced UI components with:
   - Card-like containers for content
   - Better spacing and margins
   - Improved font styling and sizing
   - Consistent color scheme across all elements

4. Improved visual hierarchy with:
   - More prominent headings
   - Better contrast for important information
   - Colored indicators for price changes and status

5. Added UI polish with:
   - Rounded corners
   - Subtle borders
   - Consistent spacing
   - Better use of whitespace

## Theme Colors:

- Background: #1E1E2E (Dark blue-purple)
- Card Background: #2A2A3C (Slightly lighter than background)
- Primary: #6272A4 (Medium purple-blue)
- Accent: #BD93F9 (Bright purple)
- Text: #F8F8F2 (Off-white)
- Success: #50FA7B (Bright green)
- Error: #FF5555 (Bright red)
- Warning: #FFB86C (Orange)

## Usage:

The dark theme is applied automatically when the application starts.

## Notes:

- Added UI assets folder for icons and images
- Updated all tables to use alternating row colors for better readability
- Implemented consistent styling for all dialogs and forms
