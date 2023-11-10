from . import supabaseClient


async def upload(uploadPath: str, filePath: str, content_type: str) -> str:
    """
    This function is used to upload file to supabase storage

    Args:
        uploadPath (str): The path of the file in supabase storage
        filePath (str): The path of the file in local

    Returns:
        str: the public url of the file
    """
    with open(filePath, "rb") as f:
        result = (
            supabaseClient.storage.from_("storage")
            .upload(uploadPath, f.read(), {"content-type": content_type})
            .json()
        )
        return supabaseClient.storage.from_("").get_public_url(result["Key"])
