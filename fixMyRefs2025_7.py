#fixMyRefs 2025.7
# Copyright (c) 2025 Giuseppe Pagnozzi
# It's licensed under the MIT License
# visit https://opensource.org/licenses/MIT for the full terms.
"""
fixMyRefs - Maya Reference Relinker Tool

Description:
This tool helps identify and fix broken references in Autodesk Maya by scanning
directories for missing reference files. It supports batch relinking using a single
directory or individual file paths. 
"""

import maya.cmds as cmds
import os
import re

copy_suffix_pattern = re.compile(r"(.+)({\d+})$")

show_all_state = [False]
use_single_path_state = [True] 
relink_log = []
original_paths = {}
relinked_refs = set()

def show_fixMyRefs_ui():
    """Creates a UI to view and relink broken references in Maya."""
    global original_paths
    if cmds.window("fixMyRefsWindow", exists=True):
        cmds.deleteUI("fixMyRefsWindow")

    all_refs = [ref for ref in cmds.ls(type="reference") if "sharedReferenceNode" not in ref]
    original_paths = {ref: cmds.referenceQuery(ref, filename=True) for ref in all_refs}

    window = cmds.window("fixMyRefsWindow", title="fixMyRefs v1")
    populate_ui(window)
    cmds.showWindow(window)


def populate_ui(window):
    """Populates the UI with references based on the 'Show all references' state and the relink log."""
    global show_all_state, use_single_path_state, relink_log, original_paths, relinked_refs

    if cmds.columnLayout("mainLayout", exists=True):
        cmds.deleteUI("mainLayout")
    
    cmds.setParent(window)
    cmds.columnLayout("mainLayout", adjustableColumn=True)

    cmds.checkBox(
        label="Show all references",
        value=show_all_state[0],
        changeCommand=lambda val: on_show_all_changed(val, window)
    )

    cmds.checkBox(
        label="Use Single Path for All Broken References",
        value=use_single_path_state[0],
        changeCommand=lambda val: on_use_single_path_changed(val, window)
    )

    all_refs = [ref for ref in cmds.ls(type="reference") if "sharedReferenceNode" not in ref] or []

    if show_all_state[0]:
        refs_to_display = all_refs
    else:
        refs_to_display = [ref for ref in all_refs if not cmds.referenceQuery(ref, isLoaded=True)]

    if not refs_to_display:
        if show_all_state[0]:
            cmds.text(label="No references found.")
        else:
            cmds.text(label="All references are valid.")
        cmds.button(label="Close", command=lambda *args: cmds.deleteUI("fixMyRefsWindow"))
        return

    dir_only_checkbox = cmds.checkBox(label="Specify Directory Only (Ignore Asset Name)", value=True)
    slash_convert_checkbox = cmds.checkBox(label="Convert Backslashes to Forward Slashes (\\ to /)", value=True)

    if use_single_path_state[0]:
        cmds.text(label="Single Path for All Broken References:")
        cmds.textField("singlePathField")
        cmds.button(
            label="Browse",
            command=lambda *args: browse_for_file("singlePathField", dir_only_checkbox)
        )

    cmds.separator()

    mapping_dict = {}

    for ref in refs_to_display:
        is_fixed = cmds.referenceQuery(ref, isLoaded=True)
        
        bg_color = (0.5, 1.0, 0.5) if is_fixed else (1.0, 1.0, 1.0)

        cmds.text(label=f"Reference: {ref}", backgroundColor=bg_color)

        if is_fixed:
            path = cmds.referenceQuery(ref, filename=True)
            cmds.text(label=f"Current Path: {path}", backgroundColor=bg_color)
        else:
            path = cmds.referenceQuery(ref, filename=True, unresolvedName=True)
            cmds.text(label=f"Invalid Path: {path}", backgroundColor=bg_color)

        status_label = "Valid" if is_fixed else "Broken"
        cmds.text(label=f"Status: {status_label}", backgroundColor=bg_color)

        if not is_fixed and not use_single_path_state[0]:
            text_field = cmds.textField()
            cmds.button(
                label="Browse",
                command=lambda *args, tf=text_field, cb=dir_only_checkbox: browse_for_file(tf, cb)
            )
            mapping_dict[ref] = text_field
        
        cmds.separator()

    cmds.rowLayout(numberOfColumns=3)
    cmds.button(
        label="Relink",
        command=lambda *args: relink_references(mapping_dict, dir_only_checkbox, slash_convert_checkbox, window)
    )
    cmds.button(label="Refresh", command=lambda *args: populate_ui(window))
    cmds.button(label="Cancel", command=lambda *args: cmds.deleteUI("fixMyRefsWindow"))
    cmds.setParent("..")

    if show_all_state[0]:
        cmds.button(label="Show Paths", command=lambda *args: show_paths_popup(mapping_dict))

    cmds.text(label="Relink Log:")
    if relink_log:
        cmds.textScrollList("relinkLogList", append=relink_log[::-1], height=100)
    else:
        cmds.text(label="No relink actions yet.")


def on_show_all_changed(val, window):
    """Updates the state and refreshes the UI when the 'Show all references' checkbox is toggled."""
    show_all_state[0] = val
    populate_ui(window)

def on_use_single_path_changed(val, window):
    """Updates the state and refreshes the UI when the 'Use Single Path' checkbox is toggled."""
    use_single_path_state[0] = val
    populate_ui(window)

def browse_for_file(text_field, dir_only_checkbox):
    """Opens a file or directory dialog based on the checkbox state and updates the text field."""
    dir_only = cmds.checkBox(dir_only_checkbox, query=True, value=True)
    if dir_only:
        dir_path = cmds.fileDialog2(fileMode=2, caption="Select directory for reference files")
        if dir_path:
            cmds.textField(text_field, edit=True, text=dir_path[0])
    else:
        file_path = cmds.fileDialog2(fileMode=1, caption="Select new reference file", fileFilter="Maya Files (*.ma *.mb)")
        if file_path:
            cmds.textField(text_field, edit=True, text=file_path[0])

def find_file_in_directory(search_dir, file_name):
    """Searches for a file with the given name in the specified directory and its subdirectories."""
    for root, _, files in os.walk(search_dir):
        if file_name in files:
            return os.path.join(root, file_name)
    return None

def convert_slashes(path, convert_to_forward):
    """Converts backslashes to forward slashes if convert_to_forward is True."""
    if convert_to_forward:
        return path.replace("\\", "/")
    return path


def relink_references(mapping_dict, dir_only_checkbox, slash_convert_checkbox, window):
    """Attempts to fixMyRefs using the new paths from the text fields and auto-refreshes the UI."""
    global relink_log, relinked_refs, copy_suffix_pattern
    dir_only = cmds.checkBox(dir_only_checkbox, query=True, value=True)
    convert_to_forward = cmds.checkBox(slash_convert_checkbox, query=True, value=True)
    success = []
    failed = []

    broken_refs = [ref for ref in cmds.ls(type="reference") if "sharedReferenceNode" not in ref and not os.path.exists(cmds.referenceQuery(ref, filename=True))]

    if use_single_path_state[0]:
        if cmds.textField("singlePathField", exists=True):
            single_path = cmds.textField("singlePathField", query=True, text=True).strip()
            if single_path:
                single_path = convert_slashes(single_path, convert_to_forward)
                for ref in broken_refs:
                    if not cmds.objExists(ref):
                        print(f"Skipping {ref}: Reference node no longer exists.")
                        continue
                    new_path = None
                    if dir_only:
                        original_path = cmds.referenceQuery(ref, filename=True, unresolvedName=True)
                        file_name_raw = os.path.basename(original_path)
                        clean_file_name = file_name_raw
                        match = copy_suffix_pattern.match(file_name_raw)
                        if match:
                            clean_file_name = match.group(1)
                        found_path = find_file_in_directory(single_path, clean_file_name)
                        if found_path:
                            new_path = found_path
                        else:
                            reason = f"Could not find '{clean_file_name}' in {single_path} (and subdirs)"
                            failed.append(f"{ref}: {reason}")
                            relink_log.append(f"Failed to relink {ref}: {reason}")
                            continue
                    else:
                        new_path = single_path
                    if new_path and os.path.exists(new_path):
                        try:
                            cmds.file(new_path, loadReference=ref)
                            is_now_loaded = cmds.referenceQuery(ref, isLoaded=True)
                            
                            if is_now_loaded:
                                current_resolved_path = cmds.referenceQuery(ref, filename=True, unresolvedName=False) 
                                success.append(ref)
                                relink_log.append(f"Successfully relinked {ref} to {current_resolved_path}")
                                relinked_refs.add(ref)
                            else:
                                current_resolved_path = cmds.referenceQuery(ref, filename=True, unresolvedName=False)
                                reason = f"Verification failed (Loaded: {is_now_loaded}, Path: '{current_resolved_path}')"
                                failed.append(f"{ref}: {reason}")
                                relink_log.append(f"Failed to relink {ref}: {reason}")
                        except Exception as e:
                            reason = f"Error: {str(e)}"
                            failed.append(f"{ref}: {reason}")
                            relink_log.append(f"Failed to relink {ref}: {reason}")
                    else:
                        reason = f"Target path does not exist: '{new_path}'"
                        failed.append(f"{ref}: {reason}")
                        relink_log.append(f"Failed to relink {ref}: {reason}")
    else:
        for ref, text_field in mapping_dict.items():
            if not cmds.objExists(ref):
                print(f"Skipping {ref}: Reference node no longer exists.")
                continue
            user_input = cmds.textField(text_field, query=True, text=True).strip()
            if not user_input:
                continue
            user_input = convert_slashes(user_input, convert_to_forward)
            new_path = None
            if dir_only:
                search_dir = user_input
                if not os.path.isdir(search_dir):
                    reason = f"Provided directory does not exist: {search_dir}"
                    failed.append(f"{ref}: {reason}")
                    relink_log.append(f"Failed to relink {ref}: {reason}")
                    continue
                try:
                    original_path = cmds.referenceQuery(ref, filename=True, unresolvedName=True)
                    file_name_raw = os.path.basename(original_path)
                    clean_file_name = file_name_raw
                    match = copy_suffix_pattern.match(file_name_raw)
                    if match:
                        clean_file_name = match.group(1)
                    found_path = find_file_in_directory(search_dir, clean_file_name)
                    if found_path:
                        new_path = found_path
                    else:
                        reason = f"Could not find '{clean_file_name}' in {search_dir} (and subdirs)"
                        failed.append(f"{ref}: {reason}")
                        relink_log.append(f"Failed to relink {ref}: {reason}")
                        continue
                except Exception as e:
                    reason = f"Error processing path: {e}"
                    failed.append(f"{ref}: {reason}")
                    relink_log.append(f"Failed to relink {ref}: {reason}")
                    continue
            else:
                new_path = user_input
            if new_path and os.path.exists(new_path):
                try:
                    cmds.file(new_path, loadReference=ref)
                    is_now_loaded = cmds.referenceQuery(ref, isLoaded=True)
                    
                    if is_now_loaded:
                        current_resolved_path = cmds.referenceQuery(ref, filename=True, unresolvedName=False) 
                        success.append(ref)
                        relink_log.append(f"Successfully relinked {ref} to {current_resolved_path}")
                        relinked_refs.add(ref)
                    else:
                        current_resolved_path = cmds.referenceQuery(ref, filename=True, unresolvedName=False)
                        reason = f"Verification failed (Loaded: {is_now_loaded}, Path: '{current_resolved_path}')"
                        failed.append(f"{ref}: {reason}")
                        relink_log.append(f"Failed to relink {ref}: {reason}")
                except Exception as e:
                    reason = f"Error: {str(e)}"
                    failed.append(f"{ref}: {reason}")
                    relink_log.append(f"Failed to relink {ref}: {reason}")
            else:
                reason = f"Target path does not exist: '{new_path}'"
                failed.append(f"{ref}: {reason}")
                relink_log.append(f"Failed to relink {ref}: {reason}")

    message = ""
    if success:
        message += "Successfully relinked:\n" + "\n".join(success) + "\n\n"
    if failed:
        message += "Failed to relink:\n" + "\n".join(failed)
    if message:
        max_len = 1000
        if len(message) > max_len:
            message = message[:max_len] + "\n...(message truncated)"
        cmds.confirmDialog(title="Relink Results", message=message, button=["OK"])

    populate_ui(window)



def show_paths_popup(mapping_dict):
    """Displays a popup with old and new paths for all references in the specified format."""
    path_text = ""
    for ref in original_paths:
        old_path = original_paths[ref]
        if ref in relinked_refs:
            current_path = cmds.referenceQuery(ref, filename=True) if cmds.objExists(ref) else "Reference removed"
            path_text += f"{old_path}\n{current_path}\n\n"
        else:
            path_text += f"{old_path}\n\n"
    
    if cmds.window("pathsWindow", exists=True):
        cmds.deleteUI("pathsWindow")
    paths_window = cmds.window("pathsWindow", title="Reference Paths", widthHeight=(500, 300))
    cmds.columnLayout(adjustableColumn=True)
    cmds.text(label="Old Path\nNew Path (if relinked)\n", align="left")
    cmds.scrollField(text=path_text, editable=True, wordWrap=False, height=250)
    cmds.button(label="Close", command=lambda *args: cmds.deleteUI(paths_window))
    cmds.showWindow(paths_window)

show_fixMyRefs_ui()