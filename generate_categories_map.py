import os
import json
import re
import subprocess
from pathlib import Path

def create_meaningful_key(filename, resource_type='audio'):
    """Extract meaningful text from filename and create a clean key."""
    # Remove file extension and convert to lowercase
    name = os.path.splitext(filename)[0].lower()

    # Remove numbers and special characters, keep only letters and spaces
    name = re.sub(r'[^a-z\s]', ' ', name)

    # Remove common words that don't add meaning
    common_words = {
        'background', 'music', 'for', 'and', 'the', 'with', 'from', 'that', 'this',
        'short', 'video', 'vlog', 'ad', 'advertising', 'sound', 'effect', 'track',
        'free', 'copyright', 'royalty', 'no', 'of', 'in', 'on', 'at', 'to', 'by', 'a', 'an',
        'animation', 'anim', 'js', 'motion', 'graphics'
    }

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
        return f"{resource_type[:4]}_{hash_str}"

    # Join with underscores for better readability
    key = '_'.join(words)

    # Ensure the key is not a common placeholder
    if key in {'untitled', 'null', 'undefined', 'none', 'empty', 'default'}:
        key = f"{resource_type[:4]}_{key}"

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
            return f'https://raw.githubusercontent.com/{repo_path}/main'
        elif repo_url.startswith('https://github.com/'):
            repo_path = repo_url.replace('https://github.com/', '').replace('.git', '')
            return f'https://raw.githubusercontent.com/{repo_path}/main'
    except (subprocess.CalledProcessError, Exception) as e:
        print(f"Warning: Could not determine repository URL: {e}")

    # Fallback to the hardcoded URL if git command fails
    return 'https://raw.githubusercontent.com/OutfinityResearch/mediaResources/main'

def get_resource_map(categories_dir, repo_base_url, resource_type, file_extensions):
    """Generate a map for a specific resource type (e.g., audio, animations)."""
    resource_map = {}

    # Walk through the categories directory
    for category_dir in os.listdir(categories_dir):
        category_path = os.path.join(categories_dir, category_dir)
        if not os.path.isdir(category_path):
            continue

        resource_dir_path = os.path.join(category_path, resource_type)

        # Skip if resource directory doesn't exist
        if not os.path.exists(resource_dir_path):
            continue

        category_map = {}
        used_keys = set()

        # Get all resource files in the category's resource directory
        try:
            resource_files = [f for f in os.listdir(resource_dir_path)
                            if f.lower().endswith(file_extensions)]

            for f in resource_files:
                key = create_meaningful_key(f, resource_type)

                # Ensure key is unique within the category
                original_key = key
                counter = 1
                while key in used_keys:
                    key = f"{original_key}_{counter}"
                    counter += 1

                used_keys.add(key)
                category_map[key] = f"{repo_base_url}/categories/{category_dir}/{resource_type}/{f}"

            if category_map:  # Only add non-empty categories
                resource_map[category_dir] = category_map

        except Exception as e:
            print(f"Error processing category {category_dir} for {resource_type}: {e}")
            continue

    return resource_map

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the categories directory
    categories_dir = os.path.join(script_dir, 'categories')

    # Get the repository base URL
    repo_base_url = get_repo_base_url()

    # --- Generate Audio Map ---
    print("Generating audio map...")
    audio_map = get_resource_map(
        categories_dir,
        repo_base_url,
        'audio',
        ('.mp3', '.wav', '.ogg', '.m4a')
    )

    # Write the audio map to a JSON file
    audio_output_file = os.path.join(script_dir, 'audio_map.json')
    with open(audio_output_file, 'w') as f:
        json.dump(audio_map, f, indent=2)
    print(f"Audio map generated successfully at: {audio_output_file}")

    # --- Generate Animations Map ---
    print("\nGenerating animations map...")
    animations_map = get_resource_map(
        categories_dir,
        repo_base_url,
        'animations',
        ('.js', '.json', '.gif')  # Include JavaScript, JSON (Lottie), and GIF files
    )

    # Write the animations map to a JSON file
    animations_output_file = os.path.join(script_dir, 'animations_map.json')
    with open(animations_output_file, 'w') as f:
        json.dump(animations_map, f, indent=2)
    print(f"Animations map generated successfully at: {animations_output_file}")

if __name__ == "__main__":
    main()
