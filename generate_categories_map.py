import os
import json
import re
import subprocess
from pathlib import Path

def create_meaningful_key(filename):
    """Extract meaningful text from filename and create a clean key."""
    # Remove file extension and convert to lowercase
    name = os.path.splitext(filename)[0].lower()

    # Remove numbers and special characters, keep only letters and spaces
    name = re.sub(r'[^a-z\s]', ' ', name)

    # Remove common words that don't add meaning
    common_words = {'background', 'music', 'for', 'and', 'the', 'with', 'from', 'that', 'this',
                   'short', 'video', 'vlog', 'ad', 'advertising', 'sound', 'effect', 'track',
                   'free', 'copyright', 'royalty', 'no', 'of', 'in', 'on', 'at', 'to', 'by', 'a', 'an'}

    # Split into words, filter out common words and empty strings
    words = [word for word in name.split() if word and word not in common_words]

    # If no meaningful words found, use parts of the original filename
    if not words:
        # Try to extract words from camelCase or snake_case
        name = re.sub(r'[^a-z]', ' ', filename.lower())
        words = [word for word in name.split() if word and word not in common_words]

    # If still no words, use a prefix with a hash of the original name
    if not words:
        import hashlib
        hash_str = hashlib.md5(filename.encode()).hexdigest()[:6]
        return f"audio_{hash_str}"

    # Join with underscores for better readability
    key = '_'.join(words)

    # Ensure the key is not a common placeholder
    if key in {'untitled', 'null', 'undefined', 'none', 'empty', 'default'}:
        key = f"audio_{key}"

    return key

def get_repo_base_url():
    """Get the GitHub repository base URL in raw format."""
    try:
        # Get the remote origin URL
        repo_url = subprocess.check_output(
            ['git', 'config', '--get', 'remote.origin.url'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        # Convert SSH to HTTPS if needed
        if repo_url.startswith('git@github.com:'):
            repo_path = repo_url.replace('git@github.com:', '').replace('.git', '')
            return f'https://raw.githubusercontent.com/{repo_path}/master'
        elif repo_url.startswith('https://github.com/'):
            repo_path = repo_url.replace('https://github.com/', '').replace('.git', '')
            return f'https://raw.githubusercontent.com/{repo_path}/master'
    except (subprocess.CalledProcessError, Exception) as e:
        print(f"Warning: Could not determine repository URL: {e}")

    # Fallback to the hardcoded URL if git command fails
    return 'https://raw.githubusercontent.com/OutfinityResearch/mediaResources/master'

def get_audio_map(audio_dir, repo_base_url):
    audio_map = {}

    # Walk through the categories directory
    for category_dir in os.listdir(audio_dir):
        category_path = os.path.join(audio_dir, category_dir)
        if not os.path.isdir(category_path):
            continue

        audio_dir_path = os.path.join(category_path, 'audio')

        # Skip if audio directory doesn't exist
        if not os.path.exists(audio_dir_path):
            continue

        category_map = {}
        used_keys = set()

        # Get all audio files in the category's audio directory
        try:
            audio_files = [f for f in os.listdir(audio_dir_path)
                         if f.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a'))]

            for f in audio_files:
                key = create_meaningful_key(f)

                # Ensure key is unique within the category
                original_key = key
                counter = 1
                while key in used_keys:
                    key = f"{original_key}_{counter}"
                    counter += 1

                used_keys.add(key)
                category_map[key] = f"{repo_base_url}/categories/{category_dir}/audio/{f}"

            if category_map:  # Only add non-empty categories
                audio_map[category_dir] = category_map

        except Exception as e:
            print(f"Error processing category {category_dir}: {e}")
            continue

    return audio_map

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the audio directory to the categories directory
    audio_dir = os.path.join(script_dir, 'categories')

    # Get the repository base URL
    repo_base_url = get_repo_base_url()

    # Generate the audio map
    audio_map = get_audio_map(audio_dir, repo_base_url)

    # Write the audio map to a JSON file
    output_file = os.path.join(script_dir, 'audio_map.json')
    with open(output_file, 'w') as f:
        json.dump(audio_map, f, indent=2)

    print(f"Audio map generated successfully at: {output_file}")

if __name__ == "__main__":
    main()
