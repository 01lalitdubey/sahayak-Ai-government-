from typing import Optional
from fastapi import Request, Query

def get_language(
    request: Request,
    lang: Optional[str] = Query(None, description="Preferred language code (e.g., 'hi')")
) -> str:
    """
    Determine the requested language in this priority:
    1. Query Parameter `?lang=hi`
    2. Accept-Language Header (simplified extraction)
    3. Default to 'en'
    """
    if lang:
        return lang.lower()
        
    accept_lang = request.headers.get("Accept-Language")
    if accept_lang:
        # Simplistic parsing: take the first language subtag
        primary_lang = accept_lang.split(',')[0].split('-')[0].lower()
        return primary_lang
        
    return "en"
