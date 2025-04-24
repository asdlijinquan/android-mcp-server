from adbdevicemanager import AdbDeviceManager
from mcp.server.fastmcp import FastMCP, Image
import os
import sys
import yaml

CONFIG_FILE = "config.yaml"
CONFIG_FILE_EXAMPLE = "config.yaml.example"

# Check if config file exists
if not os.path.exists(CONFIG_FILE):
    print(f"Config file {CONFIG_FILE} not found. Please create it from {CONFIG_FILE_EXAMPLE}.", file=sys.stderr)
    sys.exit(1)

# Load config file
with open(CONFIG_FILE) as f:
    config = yaml.safe_load(f.read())
    device_name = config["device"]["name"]

# Initialize MCP and device manager
# Error checking is done inside AdbDeviceManager's constructor
mcp = FastMCP("android")
deviceManager = AdbDeviceManager(device_name)

@mcp.tool()
def get_packages() -> str:
    """
    Get all installed packages on the device
    Returns:
        str: A list of all installed packages on the device as a string
    """
    result = deviceManager.get_packages()
    return result

@mcp.tool()
def execute_adb_shell_command(command: str) -> str:
    """Executes an ADB command and returns the output or an error.
    Args:
        command (str): The ADB shell command to execute
    Returns:
        str: The output of the ADB command
    """
    result = deviceManager.execute_adb_shell_command(command)
    return result

@mcp.tool()
def get_uilayout() -> str:
    """
    Retrieves information about clickable elements in the current UI.
    Returns a formatted string containing details about each clickable element,
    including its text, content description, bounds, and center coordinates.

    Returns:
        str: A formatted list of clickable elements with their properties
    """
    result = deviceManager.get_uilayout()
    return result


@mcp.tool()
def get_screenshot() -> Image:
    """Takes a screenshot of the device and returns it.
    Returns:
        Image: the screenshot
    """
    deviceManager.take_screenshot()
    return Image(path="compressed_screenshot.png")


@mcp.tool()
def get_package_action_intents(package_name: str) -> list[str]:
    """
    Get all non-data actions from Activity Resolver Table for a package
    Args:
        package_name (str): The name of the package to get actions for
    Returns:
        list[str]: A list of all non-data actions from the Activity Resolver Table for the package
    """
    result = deviceManager.get_package_action_intents(package_name)
    return result


@mcp.tool()
def get_network_traffic() -> str:
    """
    Get overall network traffic statistics from the device
    Returns:
        str: A formatted string containing network traffic information
    """
    result = deviceManager.get_network_traffic()
    return result


@mcp.tool()
def get_app_network_usage(package_name: str = None, uid: str = None) -> str:
    """
    Get network usage information for a specific app or all apps
    Args:
        package_name (str, optional): The package name of the app to query
        uid (str, optional): The UID of the app to query
    Returns:
        str: A formatted string containing app network usage information
    """
    result = deviceManager.get_app_network_usage(package_name, uid)
    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
