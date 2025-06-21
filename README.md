# fixMyRefs for Autodesk Maya
This tool helps you quickly find and relink broken file references in Autodesk Maya. It simplifies the process of fixing paths by allowing you to batch-relink all missing files from a single directory or handle each one individually.

---
### [Watch how it works on YouTube](https://youtu.be/IYMqPPb-pCg)
[![Watch the video](https://img.youtube.com/vi/IYMqPPb-pCg/maxresdefault.jpg)](https://youtu.be/IYMqPPb-pCg)



---

## Features

-   **Automatic Broken Reference Detection:** 
    -   On launch, the tool automatically scans your scene and lists all references with invalid or broken file paths.
-   **Batch Relinking:**
    -   **Single Path Mode:** Fix all broken references at once using a single path.
    -   **Directory Search:** Instead of a full file path, you can specify just a directory. The tool will intelligently search that directory and all its subdirectories to find the correct file for each broken reference.
-   **Flexible Views:**
    -   Toggle between viewing only **broken** references or **all** references in the scene.
    -   Switch between batch relinking (`Use Single Path`) and individual relinking modes.
-   **Path Management:**
    -   Automatically converts backslashes (`\`) to forward slashes (`/`) for better cross-platform compatibility.
-   **Feedback and Logging:**
    -   The UI provides color-coding for valid (green) and broken references.
    -   A persistent **Relink Log** shows the history of successful and failed relink attempts.
    -   A "Show Paths" feature provides a convenient pop-up to copy/paste old and new paths.

## Why it's Useful

Managing file paths in Maya can be a challenge when project folders are moved, archived, or transferred between users. 
The problem is even worse when you inherit a scene where the entire file structure is completely different from your own.

This is where fixMyRefs is most powerful. 
Instead of hunting for each missing file, you simply point the tool to the main asset directory. 
It does the searching for you, saving significant time. 



## How to Install and Run

1.  **Open Maya Script Editor:** In Autodesk Maya, open the Script Editor (**Windows → General Editors → Script Editor**).
2.  **Open Script:** In the Script Editor, go to **File → Open Script...** and navigate to select the downloaded `fixMyRefs.py` file.
3.  **Set to Python:** Ensure the tab in the Script Editor is set to "Python".
4.  **Execute:** Execute the script by clicking the "Execute All" button (looks like a double play icon) or by pressing **Ctrl + Enter** (Windows/Linux) or **Cmd + Enter** (macOS).
5.  The "fixMyRefs" UI window will appear, automatically listing any broken references found in your scene.


