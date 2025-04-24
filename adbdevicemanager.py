from ppadb.client import Client as AdbClient
import subprocess
import os
import sys
from PIL import Image as PILImage

class AdbDeviceManager:
    def __init__(self, device_name: str, exit_on_error: bool = True) -> None:
        """
        Initialize the ADB Device Manager
        
        Args:
            device_name: Name/serial of the device to manage
            exit_on_error: Whether to exit the program if device initialization fails
        """
        if not self.check_adb_installed():
            error_msg = "adb is not installed or not in PATH. Please install adb and ensure it is in your PATH."
            if exit_on_error:
                print(error_msg, file=sys.stderr)
                sys.exit(1)
            else:
                raise RuntimeError(error_msg)
        
        available_devices = self.get_available_devices()
        if not available_devices:
            error_msg = "No devices connected. Please connect a device and try again."
            if exit_on_error:
                print(error_msg, file=sys.stderr)
                sys.exit(1)
            else:
                raise RuntimeError(error_msg)
                
        if device_name not in available_devices:
            error_msg = f"Device {device_name} not found. Available devices: {available_devices}"
            if exit_on_error:
                print(error_msg, file=sys.stderr)
                sys.exit(1)
            else:
                raise RuntimeError(error_msg)
        
        # Initialize the device
        self.device = AdbClient().device(device_name)

    @staticmethod
    def check_adb_installed() -> bool:
        """Check if ADB is installed on the system."""
        try:
            subprocess.run(["adb", "version"], check=True, stdout=subprocess.PIPE)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    @staticmethod
    def get_available_devices() -> list[str]:
        """Get a list of available devices."""
        return [device.serial for device in AdbClient().devices()]
    
    def get_packages(self) -> str:
        command = "pm list packages"
        packages = self.device.shell(command).strip().split("\n")
        result = [package[8:] for package in packages]
        output = "\n".join(result)
        return output

    def get_package_action_intents(self, package_name: str) -> list[str]:
        command = f"dumpsys package {package_name}"
        output = self.device.shell(command)

        resolver_table_start = output.find("Activity Resolver Table:")
        if resolver_table_start == -1:
            return []
        resolver_section = output[resolver_table_start:]

        non_data_start = resolver_section.find("\n  Non-Data Actions:")
        if non_data_start == -1:
            return []

        section_end = resolver_section[non_data_start:].find("\n\n")
        if section_end == -1:
            non_data_section = resolver_section[non_data_start:]
        else:
            non_data_section = resolver_section[
                non_data_start : non_data_start + section_end
            ]

        actions = []
        for line in non_data_section.split("\n"):
            line = line.strip()
            if line.startswith("android.") or line.startswith("com."):
                actions.append(line)

        return actions

    def execute_adb_shell_command(self, command: str) -> str:
        """Executes an ADB command and returns the output."""
        if command.startswith("adb shell "):
            command = command[10:]
        elif command.startswith("adb "):
            command = command[4:]
        result = self.device.shell(command)
        return result

    def take_screenshot(self) -> None:
        self.device.shell("screencap -p /sdcard/screenshot.png")
        self.device.pull("/sdcard/screenshot.png", "screenshot.png")
        self.device.shell("rm /sdcard/screenshot.png")

        # compressing the ss to avoid "maximum call stack exceeded" error on claude desktop
        with PILImage.open("screenshot.png") as img:
            width, height = img.size
            new_width = int(width * 0.3)
            new_height = int(height * 0.3)
            resized_img = img.resize(
                (new_width, new_height), PILImage.Resampling.LANCZOS
            )

            resized_img.save(
                "compressed_screenshot.png", "PNG", quality=85, optimize=True
            )

    def get_uilayout(self) -> str:
        self.device.shell("uiautomator dump")
        self.device.pull("/sdcard/window_dump.xml", "window_dump.xml")
        self.device.shell("rm /sdcard/window_dump.xml")

        import xml.etree.ElementTree as ET
        import re

        def calculate_center(bounds_str):
            matches = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
            if len(matches) == 2:
                x1, y1 = map(int, matches[0])
                x2, y2 = map(int, matches[1])
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                return center_x, center_y
            return None

        tree = ET.parse("window_dump.xml")
        root = tree.getroot()

        clickable_elements = []
        for element in root.findall(".//node[@clickable='true']"):
            text = element.get("text", "")
            content_desc = element.get("content-desc", "")
            bounds = element.get("bounds", "")

            # Only include elements that have either text or content description
            if text or content_desc:
                center = calculate_center(bounds)
                element_info = "Clickable element:"
                if text:
                    element_info += f"\n  Text: {text}"
                if content_desc:
                    element_info += f"\n  Description: {content_desc}"
                element_info += f"\n  Bounds: {bounds}"
                if center:
                    element_info += f"\n  Center: ({center[0]}, {center[1]})"
                clickable_elements.append(element_info)

        if not clickable_elements:
            return "No clickable elements found with text or description"
        else:
            result = "\n\n".join(clickable_elements)
            return result

    def get_network_traffic(self) -> str:
        """Gets overall network traffic statistics from the device.
        
        Returns:
            str: A formatted string containing network traffic information
        """
        try:
            # Get general network stats
            netstats_output = self.device.shell("dumpsys netstats | grep -E 'iface=|uid=' | head -50")
            
            # Get active network interfaces
            active_ifaces = self.device.shell("dumpsys connectivity | grep -E 'type: WIFI|type: MOBILE' | head -10")
            
            # Format the output
            result = "=== NETWORK TRAFFIC INFORMATION ===\n\n"
            result += "== ACTIVE INTERFACES ==\n"
            result += active_ifaces + "\n\n"
            result += "== TRAFFIC STATISTICS ==\n"
            result += netstats_output
            
            return result
        except Exception as e:
            return f"Error retrieving network traffic information: {str(e)}"

    def get_app_network_usage(self, package_name=None, uid=None) -> str:
        """Gets network usage information for a specific app or all apps.
        
        Args:
            package_name (str, optional): The package name of the app to query.
            uid (str, optional): The UID of the app to query.
            
        Returns:
            str: A formatted string containing app network usage information
        """
        try:
            result = "=== APP NETWORK USAGE ===\n\n"
            
            # If no specific package or UID provided, list all apps with their UIDs
            if not package_name and not uid:
                # Get all packages with network usage permissions
                netpolicy_output = self.device.shell("dumpsys netpolicy | grep -E 'UID='")
                result += "== APPS WITH NETWORK POLICIES ==\n"
                result += netpolicy_output + "\n\n"
                
                # Get top network usage consumers
                top_consumers = self.device.shell("dumpsys netstats | grep -E 'package=' | head -20")
                result += "== TOP NETWORK CONSUMERS ==\n"
                result += top_consumers
                
                return result
            
            # Get specific app's info
            uid_filter = f"uid={uid}" if uid else ""
            package_filter = f"package={package_name}" if package_name else ""
            grep_filter = uid_filter or package_filter
            
            # Get app network stats
            if grep_filter:
                detail_stats = self.device.shell(f"dumpsys netstats detail | grep -A 30 '{grep_filter}' | grep -v 'uid=[0-9]\\{{5\\}}' | head -50")
                result += f"== DETAILED NETWORK STATS FOR {package_name or f'UID {uid}'} ==\n"
                result += detail_stats
            
            return result
        except Exception as e:
            return f"Error retrieving app network usage information: {str(e)}"
