"""Sharing utilities for uploading recordings to hosting services."""
from pathlib import Path
import base64
import json
from typing import Optional

# Only import requests if available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class ShareError(Exception):
    """Error during sharing/upload."""
    pass


def check_requests():
    """Check if requests library is available."""
    if not HAS_REQUESTS:
        raise ShareError(
            "Sharing requires the 'requests' library. "
            "Install it with: pip install termgif[share]"
        )


def upload_imgur(
    file_path: Path,
    client_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """Upload an image/GIF to Imgur.

    Args:
        file_path: Path to the file to upload
        client_id: Imgur API client ID
        title: Optional title for the upload
        description: Optional description

    Returns:
        Dict with 'url', 'delete_hash', and 'id' keys

    Raises:
        ShareError: If upload fails
    """
    check_requests()
    file_path = Path(file_path)

    if not file_path.exists():
        raise ShareError(f"File not found: {file_path}")

    # Read and encode file
    with open(file_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    # Determine type
    suffix = file_path.suffix.lower()
    if suffix == '.gif':
        image_type = 'gif'
    elif suffix == '.mp4':
        image_type = 'video/mp4'
    elif suffix in ('.png', '.jpg', '.jpeg', '.webp'):
        image_type = 'image'
    else:
        image_type = 'image'

    # Build payload
    payload = {
        'image': image_data,
        'type': 'base64',
    }

    if title:
        payload['title'] = title
    if description:
        payload['description'] = description

    # Upload
    headers = {
        'Authorization': f'Client-ID {client_id}'
    }

    try:
        # Use video endpoint for mp4, image for others
        if suffix == '.mp4':
            url = 'https://api.imgur.com/3/upload'
            payload['type'] = 'file'
            # For video, we need to send as file
            del payload['image']
            with open(file_path, 'rb') as f:
                files = {'video': f}
                response = requests.post(
                    url,
                    headers=headers,
                    files=files,
                    data={'title': title} if title else None,
                    timeout=120
                )
        else:
            response = requests.post(
                'https://api.imgur.com/3/image',
                headers=headers,
                data=payload,
                timeout=60
            )

        response.raise_for_status()
        result = response.json()

        if not result.get('success'):
            error_msg = result.get('data', {}).get('error', 'Unknown error')
            raise ShareError(f"Imgur upload failed: {error_msg}")

        data = result['data']
        return {
            'url': data['link'],
            'delete_hash': data.get('deletehash'),
            'id': data['id'],
            'service': 'imgur'
        }

    except requests.exceptions.RequestException as e:
        raise ShareError(f"Network error during Imgur upload: {e}")


def upload_giphy(
    file_path: Path,
    api_key: str,
    tags: Optional[list[str]] = None,
    source_url: Optional[str] = None,
) -> dict:
    """Upload a GIF to Giphy.

    Args:
        file_path: Path to the GIF file
        api_key: Giphy API key
        tags: Optional list of tags
        source_url: Optional source URL

    Returns:
        Dict with 'url', 'id', and 'embed_url' keys

    Raises:
        ShareError: If upload fails
    """
    check_requests()
    file_path = Path(file_path)

    if not file_path.exists():
        raise ShareError(f"File not found: {file_path}")

    if file_path.suffix.lower() != '.gif':
        raise ShareError("Giphy only accepts GIF files")

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'image/gif')}
            data = {'api_key': api_key}

            if tags:
                data['tags'] = ','.join(tags)
            if source_url:
                data['source_post_url'] = source_url

            response = requests.post(
                'https://upload.giphy.com/v1/gifs',
                files=files,
                data=data,
                timeout=120
            )

        response.raise_for_status()
        result = response.json()

        if result.get('meta', {}).get('status') != 200:
            error_msg = result.get('meta', {}).get('msg', 'Unknown error')
            raise ShareError(f"Giphy upload failed: {error_msg}")

        data = result['data']
        gif_id = data['id']

        return {
            'url': f'https://giphy.com/gifs/{gif_id}',
            'id': gif_id,
            'embed_url': f'https://giphy.com/embed/{gif_id}',
            'service': 'giphy'
        }

    except requests.exceptions.RequestException as e:
        raise ShareError(f"Network error during Giphy upload: {e}")


def upload_catbox(file_path: Path) -> dict:
    """Upload a file to Catbox.moe (anonymous, no API key needed).

    Args:
        file_path: Path to the file to upload

    Returns:
        Dict with 'url' key

    Raises:
        ShareError: If upload fails
    """
    check_requests()
    file_path = Path(file_path)

    if not file_path.exists():
        raise ShareError(f"File not found: {file_path}")

    try:
        with open(file_path, 'rb') as f:
            files = {'fileToUpload': (file_path.name, f)}
            data = {'reqtype': 'fileupload'}

            response = requests.post(
                'https://catbox.moe/user/api.php',
                files=files,
                data=data,
                timeout=120
            )

        response.raise_for_status()
        url = response.text.strip()

        if not url.startswith('https://'):
            raise ShareError(f"Catbox upload failed: {url}")

        return {
            'url': url,
            'service': 'catbox'
        }

    except requests.exceptions.RequestException as e:
        raise ShareError(f"Network error during Catbox upload: {e}")


def upload(
    file_path: Path,
    service: str = "catbox",
    **kwargs
) -> dict:
    """Upload a file to a sharing service.

    Args:
        file_path: Path to the file to upload
        service: Service to use ('imgur', 'giphy', 'catbox')
        **kwargs: Service-specific arguments

    Returns:
        Dict with upload result including 'url' key

    Raises:
        ShareError: If upload fails
    """
    service = service.lower()

    if service == 'imgur':
        client_id = kwargs.get('client_id')
        if not client_id:
            raise ShareError("Imgur requires 'client_id' argument")
        return upload_imgur(
            file_path,
            client_id,
            title=kwargs.get('title'),
            description=kwargs.get('description')
        )

    elif service == 'giphy':
        api_key = kwargs.get('api_key')
        if not api_key:
            raise ShareError("Giphy requires 'api_key' argument")
        return upload_giphy(
            file_path,
            api_key,
            tags=kwargs.get('tags'),
            source_url=kwargs.get('source_url')
        )

    elif service == 'catbox':
        return upload_catbox(file_path)

    else:
        raise ShareError(f"Unknown sharing service: {service}")


def get_available_services() -> list[str]:
    """Get list of available sharing services."""
    return ['catbox', 'imgur', 'giphy']


__all__ = [
    'ShareError',
    'upload',
    'upload_imgur',
    'upload_giphy',
    'upload_catbox',
    'get_available_services',
]
