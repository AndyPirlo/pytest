import os
import tkinter as tk
from tkinter import filedialog, messagebox

class FolderSelectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("C Code Verifier")
        self.root.geometry("400x400")
        
        # List to store performed verifications
        self.verifications = []

        # Step 1: Select the HLS path
        self.folder_label = tk.Label(root, text="1. Select the HLS path:", font=("Arial", 12))
        self.folder_label.pack(pady=10)

        self.select_button = tk.Button(root, text="Browse", command=self.select_folder)
        self.select_button.pack(pady=5)

        self.selected_folder = tk.Label(root, text="No folder selected", fg="blue", font=("Arial", 10))
        self.selected_folder.pack(pady=5)

        # Step 2: Who is the SW delivery for?
        self.question_label = tk.Label(root, text="2. Who is the SW delivery for?", font=("Arial", 12))
        self.question_label.pack(pady=10)

        self.marelli_var = tk.IntVar()
        self.bhtc_var = tk.IntVar()

        self.marelli_checkbox = tk.Checkbutton(root, text="Marelli", variable=self.marelli_var)
        self.marelli_checkbox.pack(pady=5)
        
        self.bhtc_checkbox = tk.Checkbutton(root, text="BHTC", variable=self.bhtc_var)
        self.bhtc_checkbox.pack(pady=5)

        # Verify button
        self.verify_button = tk.Button(root, text="Verify", command=self.verify)
        self.verify_button.pack(pady=20)

    def select_folder(self):
        # Open folder dialog
        folder_path = filedialog.askdirectory()

    def is_valid_hls_folder(self, folder_path):
        # Check for folder containing 'C_Code', 'Calibration_CLIMBOX', and .slx file
        has_c_code_folder = any("C_Code" in folder for folder in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, folder)))
        has_calibration_folder = "Calibration_CLIMBOX" in os.listdir(folder_path)
        has_slx_file = any(file.endswith(".slx") for file in os.listdir(folder_path))
        
        return has_c_code_folder and has_calibration_folder and has_slx_file

    def verify(self):
        # Check if a folder is selected
        folder_path = self.selected_folder.cget("text")
        if folder_path == "No folder selected":
            messagebox.showerror("Error", "Please select a folder first.")
            return  # Stop further execution if no folder is selected

        # Reset verifications list for each run
        self.verifications = []

        # Flag to check if sharedutils verification is already done
        sharedutils_verified = False
        bhtc_errors = False  # New flag to track if there are any BHTC verification errors

        # Check if BHTC is selected
        if self.bhtc_var.get() == 1:
            sharedutils_verified, bhtc_errors = self.verify_bhtc()

        # Check if Marelli is selected (verify _sharedutils folder)
        if self.marelli_var.get() == 1:
            if not sharedutils_verified:
                self.verify_sharedutils_folder()

        # Check for errors; don't show the success message if there are any
        if not bhtc_errors and self.verifications:  # Only show success message if verifications were performed and no BHTC errors
            verification_list = "\n".join(["- " + v for v in self.verifications])
            messagebox.showinfo("Verification Passed", f"All verifications passed successfully!\n\nVerifications performed:\n{verification_list}")

    def verify_bhtc(self):
        folder_path = self.selected_folder.cget("text")

        # Find the C_Code folder
        c_code_folder = None
        for folder in os.listdir(folder_path):
            if "C_Code" in folder and os.path.isdir(os.path.join(folder_path, folder)):
                c_code_folder = os.path.join(folder_path, folder)
                break

        bhtc_errors = False  # Flag to track if there are any errors during BHTC verification

        if c_code_folder:
            # Verify if _sharedutils folder exists
            sharedutils_folder = os.path.join(c_code_folder, "_sharedutils")
            if os.path.exists(sharedutils_folder) and os.path.isdir(sharedutils_folder):
                self.verifications.append("Checked for _sharedutils folder.")
                # Now, verify Calibrations.c
                calibrations_file_path = os.path.join(c_code_folder, "Calibrations.c")
                if os.path.exists(calibrations_file_path):
                    if not self.check_calibrations_file(calibrations_file_path):
                        messagebox.showerror("Error", "The Calibrations.c file does not contain the required lines.")
                        bhtc_errors = True  # Set the error flag
                    else:
                        # Add to list of successful verifications
                        self.verifications.append("Checked Calibrations.c for required pragma lines.")

                # Now verify Calibrations.h
                calibrations_h_file_path = os.path.join(sharedutils_folder, "Calibrations.h")
                if os.path.exists(calibrations_h_file_path):
                    if not self.check_calibrations_h_file(calibrations_h_file_path):
                        messagebox.showerror("Error", "The Calibrations.h file does not contain the required pragma lines or the last line does not contain #endif.")
                        bhtc_errors = True  # Set the error flag
                    else:
                        self.verifications.append("Checked Calibrations.h for required pragma lines.")
                else:
                    messagebox.showerror("Error", "Calibrations.h file not found in _sharedutils folder.")
                    bhtc_errors = True  # Set the error flag
            else:
                messagebox.showerror("Error", "_sharedutils folder not found in C_Code folder.")
                return False, True  # Indicate that sharedutils verification failed with an error
        else:
            messagebox.showerror("Error", "C_Code folder not found.")
            bhtc_errors = True  # Set the error flag

        return True, bhtc_errors  # Return whether the verification passed and whether there were errors

    def verify_sharedutils_folder(self):
        folder_path = self.selected_folder.cget("text")

        # Find the C_Code folder
        c_code_folder = None
        for folder in os.listdir(folder_path):
            if "C_Code" in folder and os.path.isdir(os.path.join(folder_path, folder)):
                c_code_folder = os.path.join(folder_path, folder)
                break

        if c_code_folder:
            # Check if _sharedutils folder exists inside C_Code folder
            sharedutils_folder = os.path.join(c_code_folder, "_sharedutils")
            if os.path.exists(sharedutils_folder) and os.path.isdir(sharedutils_folder):
                # Add to list of successful verifications
                self.verifications.append("Checked for _sharedutils folder.")
            else:
                messagebox.showerror("Error", "_sharedutils folder not found in C_Code folder.")
        else:
            messagebox.showerror("Error", "C_Code folder not found.")

    def check_calibrations_file(self, file_path):
        # Lines to check in Calibrations.c
        required_lines_upper = ["#pragma ghs startdata", "#pragma ghs section rodata\".calibData\""]
        required_lines_lower = ["#pragma ghs section rodata=default", "#pragma ghs enddata"]

        with open(file_path, "r") as file:
            content = file.readlines()

        # Check if the required lines are in the file
        found_upper = all(any(required_line in line for line in content) for required_line in required_lines_upper)
        found_lower = all(any(required_line in line for line in content) for required_line in required_lines_lower)

        # Return True if both sets of lines are found
        return found_upper and found_lower

    def check_calibrations_h_file(self, file_path):
        # Lines to check in Calibrations.h
        required_lines_upper = ["#pragma ghs startdata", "#pragma ghs section rodata\".calibData\""]
        required_lines_lower = ["#pragma ghs section rodata=default", "#pragma ghs enddata"]

        with open(file_path, "r") as file:
            content = file.readlines()

        # Remove blank lines from the bottom to find the last meaningful line
        stripped_content = [line.strip() for line in content if line.strip() != '']

        # Check if the last non-blank line contains #endif
        if stripped_content and "#endif" not in stripped_content[-1]:
            return False  # Fail if the last line does not contain #endif

        # Check if the required upper lines are in the file
        found_upper = all(any(required_line in line for line in content) for required_line in required_lines_upper)
        
        # Check if the required lower lines are in the file
        found_lower = all(any(required_line in line for line in content) for required_line in required_lines_lower)

        # Return True if all checks pass
        return found_upper and found_lower

if __name__ == "__main__":
    root = tk.Tk()
    app = FolderSelectorApp(root)
    root.mainloop()
