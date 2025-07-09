import subprocess
import sys

REQUIRED_PACKAGES = [
    "requests",
    "beautifulsoup4",
    "pymongo",
    "scikit-learn",
    "scipy",
    "numpy",
    "tqdm"
]

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def main():
    print("\nInstalling required dependencies...")
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package.split('==')[0])
            print(f"\n{package} is already installed.")
        except ImportError:
            print(f"\nInstalling {package}...\n")
            install(package)
    print("\nAll dependencies are installed...\n")

if __name__ == "__main__":
    main() 