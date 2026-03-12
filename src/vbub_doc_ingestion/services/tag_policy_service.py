"""Tag policy service.

Responsibility: validate and normalise user-supplied tags at ingestion time.

Policy rules (v1):
  - None or empty input -> return empty list.
  - Each tag is lowercased and stripped of surrounding whitespace.
  - Empty strings (after stripping) are discarded.
  - Tags longer than 50 characters are rejected.
  - Lists exceeding 20 tags are rejected.
  - Duplicates are removed while preserving first-seen order.
"""

from typing import Optional

_MAX_TAGS = 20
_MAX_TAG_LENGTH = 50


def validate_tags(tags: Optional[list[str]]) -> list[str]:
    """Validate and normalise a list of user-supplied tags.

    Args:
        tags: raw tag list from the client, or None.

    Returns:
        Cleaned, deduplicated list of lowercase tag strings.

    Raises:
        ValueError: if the list exceeds the maximum count or any tag
                    exceeds the maximum character length.
    """
    if not tags:
        return []

    if len(tags) > _MAX_TAGS:
        raise ValueError(
            f"Too many tags: received {len(tags)}, maximum is {_MAX_TAGS}."
        )

    cleaned: list[str] = []
    seen: set[str] = set()

    for raw in tags:
        tag = raw.strip().lower()
        if not tag:
            continue
        if len(tag) > _MAX_TAG_LENGTH:
            raise ValueError(
                f"Tag '{tag[:20]}...' exceeds the maximum length of {_MAX_TAG_LENGTH} characters."
            )
        if tag not in seen:
            seen.add(tag)
            cleaned.append(tag)

    return cleaned
