import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

# =========================================================
# USER INPUTS
# =========================================================

# SHAREPOINT FOLDER URLS
FIRST_SHAREPOINT_URL = "https://company.sharepoint.com/sites/project/Shared%20Documents/Folder1"

SECOND_SHAREPOINT_URL = "https://company.sharepoint.com/sites/project/Shared%20Documents/Folder2"

# LOCAL FOLDERS CONTAINING ZIP FILES
FIRST_LOCAL_FOLDER = r"C:\ZIP_FOLDER_1"

SECOND_LOCAL_FOLDER = r"C:\ZIP_FOLDER_2"

# BROWSER SESSION FOLDER
SESSION_FOLDER = "browser_session"

# =========================================================
# GLOBAL LISTS
# =========================================================

uploaded_files = []
failed_files = []
skipped_files = []

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def print_line():
    print("=" * 70)


def get_zip_files(folder_path):
    """
    Return all ZIP files from folder
    """

    if not os.path.exists(folder_path):
        print(f"[ERROR] Folder not found: {folder_path}")
        return []

    zip_files = []

    for file in os.listdir(folder_path):
        full_path = os.path.join(folder_path, file)

        if os.path.isfile(full_path) and file.lower().endswith(".zip"):
            zip_files.append(full_path)

    return zip_files


def wait_for_upload_completion(page, timeout=120):
    """
    Wait for SharePoint upload to complete
    """

    start_time = time.time()

    while True:

        # Try to detect upload progress dialog
        uploading = page.locator("text=Uploading").count()

        if uploading == 0:
            break

        elapsed = time.time() - start_time

        if elapsed > timeout:
            raise Exception("Upload timeout")

        time.sleep(2)

    # Extra wait for SharePoint processing
    time.sleep(3)


def upload_single_file(page, file_path):
    """
    Upload one file to SharePoint
    """

    file_name = Path(file_path).name

    print_line()
    print(f"[UPLOADING] {file_name}")

    try:

        # -------------------------------------------------
        # CLICK UPLOAD BUTTON
        # -------------------------------------------------

        page.locator("text=Upload").first.click()

        time.sleep(2)

        # -------------------------------------------------
        # HANDLE FILE INPUT
        # -------------------------------------------------

        file_input = page.locator("input[type='file']").first

        file_input.set_input_files(file_path)

        # -------------------------------------------------
        # WAIT FOR UPLOAD
        # -------------------------------------------------

        wait_for_upload_completion(page)

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        uploaded_files.append(file_name)

        print(f"[SUCCESS] {file_name}")

    except Exception as e:

        failed_files.append(file_name)

        print(f"[FAILED] {file_name}")
        print(f"[ERROR] {str(e)}")


def upload_folder(page, sharepoint_url, local_folder):
    """
    Upload all ZIP files from local folder
    """

    print_line()
    print(f"[OPENING SHAREPOINT]")
    print(sharepoint_url)

    # -------------------------------------------------
    # OPEN SHAREPOINT FOLDER
    # -------------------------------------------------

    page.goto(sharepoint_url)

    page.wait_for_load_state("networkidle")

    time.sleep(5)

    # -------------------------------------------------
    # GET ZIP FILES
    # -------------------------------------------------

    zip_files = get_zip_files(local_folder)

    if not zip_files:
        print(f"[INFO] No ZIP files found in:")
        print(local_folder)
        return

    print_line()
    print(f"[FOUND {len(zip_files)} ZIP FILES]")
    print(local_folder)

    # -------------------------------------------------
    # UPLOAD FILES ONE BY ONE
    # -------------------------------------------------

    for file_path in zip_files:

        upload_single_file(page, file_path)

        # Small delay between uploads
        time.sleep(2)


def print_summary():
    """
    Print final summary
    """

    print_line()
    print("FINAL SUMMARY")
    print_line()

    print(f"\nTOTAL UPLOADED : {len(uploaded_files)}")

    for file in uploaded_files:
        print(f"  [OK] {file}")

    print(f"\nTOTAL FAILED : {len(failed_files)}")

    for file in failed_files:
        print(f"  [FAILED] {file}")

    print_line()


# =========================================================
# MAIN
# =========================================================

def main():

    with sync_playwright() as p:

        # -------------------------------------------------
        # PERSISTENT BROWSER SESSION
        # -------------------------------------------------

        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_FOLDER,
            headless=False
        )

        page = context.new_page()

        # -------------------------------------------------
        # FIRST TIME LOGIN
        # -------------------------------------------------

        print_line()
        print("OPENING SHAREPOINT LOGIN PAGE")

        page.goto("https://company.sharepoint.com")

        print("\nLogin manually if required.")
        input("\nAfter login press ENTER to continue...")

        # =================================================
        # FIRST FOLDER UPLOAD
        # =================================================

        upload_folder(
            page,
            FIRST_SHAREPOINT_URL,
            FIRST_LOCAL_FOLDER
        )

        # =================================================
        # SECOND FOLDER UPLOAD
        # =================================================

        upload_folder(
            page,
            SECOND_SHAREPOINT_URL,
            SECOND_LOCAL_FOLDER
        )

        # =================================================
        # FINAL SUMMARY
        # =================================================

        print_summary()

        input("\nPress ENTER to close browser...")

        context.close()


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()