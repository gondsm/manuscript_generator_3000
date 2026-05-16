INDEX_FILE_PROPERTY_VALUE = "index_file"
FILE_TYPE_PROPERTY_NAME = "type"
SHORT_FICTION_PROPERTY_VALUE = "short_fiction"

from pathlib import Path

from ..importers import markdown_importer_innards

# TODO: this shouldn't return a tuple, it should return a nice dataclass
def discover_manuscript_files(root: Path) -> list[tuple[Path, str]]:
    """Discover manuscript files based on their properties."""
    
    def matches_property(file_path: Path, property_value: str) -> bool:
        """Check if a file has the specified property value."""
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        _, properties = markdown_importer_innards.extract_properties(lines)
        
        if not properties:
            return False

        matching_key = next(
            (key for key in properties if key.lower() == FILE_TYPE_PROPERTY_NAME.lower()),
            None,
        )

        if matching_key is None:
            return False

        return str(properties[matching_key]).strip().lower() == property_value.strip().lower()
    
    # Discover manuscripts by property
    index_files = []
    for path in root.rglob("*.md"):
        if not path.is_file():
            continue

        if matches_property(path, INDEX_FILE_PROPERTY_VALUE):
            index_files.append((path, "index"))
        elif matches_property(path, SHORT_FICTION_PROPERTY_VALUE):
            index_files.append((path, "short_fiction"))

    return sorted(set(index_files))