import re
from typing import Dict, Iterable, Optional, Set, Tuple

# Canonical list for known ambiguous city/state names.
KNOWN_AMBIGUOUS_LOCATIONS: Dict[str, Set[str]] = {
    "albany": {"New York, USA", "Georgia, USA"},
    "alexandria": {"Virginia, USA", "Egypt"},
    "alton": {"Illinois, USA", "Hampshire, UK"},
    "amherst": {"Massachusetts, USA", "Nova Scotia, Canada"},
    "anderson": {"Indiana, USA", "South Carolina, USA"},
    "arlington": {"Virginia, USA", "Texas, USA"},
    "ashland": {"Oregon, USA", "Kentucky, USA"},
    "athens": {"Greece", "Georgia, USA"},
    "auburn": {"Alabama, USA", "New York, USA"},
    "augusta": {"Georgia, USA", "Maine, USA"},
    "aurora": {"Illinois, USA", "Colorado, USA"},
    "bangor": {"Maine, USA", "Wales, UK"},
    "barnesville": {"Georgia, USA", "Minnesota, USA"},
    "bath": {"Somerset, UK", "Maine, USA"},
    "bedford": {"England, UK", "Texas, USA"},
    "belmont": {"California, USA", "Massachusetts, USA"},
    "berlin": {"Germany", "Connecticut, USA"},
    "birmingham": {"England, UK", "Alabama, USA"},
    "bloomington": {"Indiana, USA", "Illinois, USA"},
    "bolton": {"England, UK", "Ontario, Canada"},
    "boston": {"Massachusetts, USA", "Lincolnshire, UK"},
    "brighton": {"England, UK", "Michigan, USA"},
    "bristol": {"England, UK", "Tennessee, USA"},
    "brookfield": {"Wisconsin, USA", "Connecticut, USA"},
    "buffalo": {"New York, USA", "Minnesota, USA"},
    "burlington": {"Vermont, USA", "Ontario, Canada"},
    "cambridge": {"England, UK", "Massachusetts, USA"},
    "camden": {"New Jersey, USA", "London, UK"},
    "canton": {"Ohio, USA", "Georgia, USA"},
    "carrollton": {"Texas, USA", "Georgia, USA"},
    "chester": {"England, UK", "Pennsylvania, USA"},
    "clinton": {"Mississippi, USA", "Iowa, USA"},
    "columbia": {"South Carolina, USA", "Missouri, USA"},
    "columbus": {"Ohio, USA", "Georgia, USA"},
    "concord": {"New Hampshire, USA", "California, USA"},
    "corinth": {"Greece", "Mississippi, USA"},
    "dallas": {"Texas, USA", "Georgia, USA"},
    "danville": {"Illinois, USA", "Virginia, USA"},
    "dayton": {"Ohio, USA", "Nevada, USA"},
    "delhi": {"India", "New York, USA"},
    "denton": {"Texas, USA", "Maryland, USA"},
    "derby": {"England, UK", "Connecticut, USA"},
    "douglas": {"Isle of Man", "Arizona, USA"},
    "dublin": {"Ireland", "USA"},
    "durham": {"England, UK", "North Carolina, USA"},
    "easton": {"Pennsylvania, USA", "Maryland, USA"},
    "eden": {"North Carolina, USA", "New South Wales, Australia"},
    "edinburgh": {"Scotland, UK", "Indiana, USA"},
    "elizabeth": {"New Jersey, USA", "Colorado, USA"},
    "elgin": {"Illinois, USA", "Scotland, UK"},
    "fairfield": {"California, USA", "Connecticut, USA"},
    "fairview": {"Oregon, USA", "Texas, USA"},
    "falmouth": {"Cornwall, UK", "Massachusetts, USA"},
    "florence": {"Italy", "South Carolina, USA"},
    "frankfort": {"Kentucky, USA", "Illinois, USA"},
    "franklin": {"Tennessee, USA", "Massachusetts, USA"},
    "frederick": {"Maryland, USA", "Colorado, USA"},
    "georgetown": {"Guyana", "Texas, USA"},
    "georgia": {"USA", "Country"},
    "glasgow": {"Scotland, UK", "Kentucky, USA"},
    "grafton": {"Massachusetts, USA", "New South Wales, Australia"},
    "greenville": {"South Carolina, USA", "North Carolina, USA"},
    "greenwich": {"England, UK", "Connecticut, USA"},
    "hamilton": {"Ontario, Canada", "New Zealand"},
    "harrison": {"New Jersey, USA", "Arkansas, USA"},
    "hastings": {"England, UK", "Nebraska, USA"},
    "hebron": {"West Bank", "Kentucky, USA"},
    "helena": {"Montana, USA", "Arkansas, USA"},
    "houston": {"Texas, USA", "Scotland, UK"},
    "hudson": {"New York, USA", "Ohio, USA"},
    "huntington": {"West Virginia, USA", "New York, USA"},
    "independence": {"Missouri, USA", "Kansas, USA"},
    "jackson": {"Mississippi, USA", "Tennessee, USA"},
    "jamestown": {"New York, USA", "North Dakota, USA"},
    "jefferson": {"Georgia, USA", "Iowa, USA"},
    "johnson city": {"Tennessee, USA", "New York, USA"},
    "kansas city": {"Missouri, USA", "Kansas, USA"},
    "kingston": {"Jamaica", "Ontario, Canada"},
    "lafayette": {"Louisiana, USA", "Colorado, USA"},
    "lancaster": {"Pennsylvania, USA", "England, UK"},
    "lebanon": {"Country", "Tennessee, USA"},
    "leeds": {"England, UK", "Alabama, USA"},
    "lexington": {"Kentucky, USA", "Massachusetts, USA"},
    "lincoln": {"England, UK", "Nebraska, USA"},
    "lisbon": {"Portugal", "Ohio, USA"},
    "liverpool": {"England, UK", "New York, USA"},
    "london": {"England, UK", "Ontario, Canada"},
    "manchester": {"England, UK", "New Hampshire, USA"},
    "mansfield": {"England, UK", "Ohio, USA"},
    "marion": {"Illinois, USA", "Iowa, USA"},
    "medina": {"Saudi Arabia", "Ohio, USA"},
    "melbourne": {"Australia", "Florida, USA"},
    "memphis": {"Tennessee, USA", "Egypt"},
    "miami": {"Florida, USA", "Oklahoma, USA"},
    "middletown": {"Connecticut, USA", "Ohio, USA"},
    "milan": {"Italy", "Michigan, USA"},
    "milford": {"Connecticut, USA", "Pennsylvania, USA"},
    "montgomery": {"Alabama, USA", "Texas, USA"},
    "moscow": {"Russia", "Idaho, USA"},
    "mount vernon": {"New York, USA", "Illinois, USA"},
    "newark": {"New Jersey, USA", "Delaware, USA"},
    "newcastle": {"England, UK", "New South Wales, Australia"},
    "newport": {"Rhode Island, USA", "Wales, UK"},
    "orlando": {"Florida, USA", "West Virginia, USA"},
    "oxford": {"England, UK", "Mississippi, USA"},
    "palermo": {"Italy", "Buenos Aires, Argentina"},
    "paris": {"France", "Texas, USA"},
    "perth": {"Western Australia, Australia", "Scotland, UK"},
    "peterborough": {"England, UK", "Ontario, Canada"},
    "plymouth": {"England, UK", "Massachusetts, USA"},
    "portland": {"Oregon, USA", "Maine, USA"},
    "preston": {"England, UK", "Idaho, USA"},
    "princeton": {"New Jersey, USA", "West Virginia, USA"},
    "richmond": {"Virginia, USA", "British Columbia, Canada"},
    "rochester": {"New York, USA", "Minnesota, USA"},
    "salem": {"Oregon, USA", "Massachusetts, USA"},
    "santiago": {"Chile", "Dominican Republic"},
    "savannah": {"Georgia, USA", "Tennessee, USA"},
    "springfield": {"Illinois, USA", "Missouri, USA"},
    "stuttgart": {"Germany", "Arkansas, USA"},
    "sydney": {"New South Wales, Australia", "Nova Scotia, Canada"},
    "troy": {"Michigan, USA", "New York, USA"},
    "trenton": {"New Jersey, USA", "Michigan, USA"},
    "valencia": {"Spain", "Venezuela"},
    "vancouver": {"Canada", "USA"},
    "victoria": {"British Columbia, Canada", "Texas, USA"},
    "warsaw": {"Poland", "Indiana, USA"},
    "washington": {"District of Columbia, USA", "England, UK"},
    "york": {"England, UK", "Pennsylvania, USA"},
}


def get_known_ambiguous_locations() -> Dict[str, Set[str]]:
    """Return a copy so callers cannot mutate global ambiguity definitions."""
    return {city: set(regions) for city, regions in KNOWN_AMBIGUOUS_LOCATIONS.items()}


def build_city_country_map(*datasets: Dict[str, Dict[str, dict]]) -> Dict[str, Set[str]]:
    """Build city->countries map from one or more country->city datasets."""
    city_countries: Dict[str, Set[str]] = {}

    for dataset in datasets:
        for country, cities in dataset.items():
            for city in cities:
                city_countries.setdefault(city.lower(), set()).add(country)

    return city_countries


def _has_explicit_qualifier(message_lower: str, city_lower: str, regions: Iterable[str]) -> bool:
    normalized_message = re.sub(r"\s*,\s*", ",", message_lower)

    # Handles full "City, State, Country" and "City, Country" inputs.
    if re.search(rf"\b{re.escape(city_lower)}\s*,\s*[^,]+\s*,\s*[^,]+\b", message_lower):
        return True

    for region in regions:
        region_lower = region.lower()
        if region_lower in message_lower:
            return True
        if f"{city_lower},{region_lower}" in normalized_message:
            return True

    return False


def detect_ambiguous_city(
    message: str,
    city_countries: Optional[Dict[str, Set[str]]] = None,
) -> Tuple[Optional[str], Optional[Set[str]]]:
    """Find ambiguous city/state mentions and return the city with possible regions."""
    message_lower = (message or "").lower()
    ambiguous_locations = get_known_ambiguous_locations()

    if city_countries:
        for city_lower, countries in city_countries.items():
            if len(countries) > 1:
                ambiguous_locations.setdefault(city_lower, set()).update(countries)

    for city_lower, regions in ambiguous_locations.items():
        if city_lower in message_lower and not _has_explicit_qualifier(message_lower, city_lower, regions):
            return city_lower, set(regions)

    return None, None


def format_ambiguity_prompt(city: str, regions: Iterable[str]) -> str:
    sorted_regions = sorted(set(regions))
    formatted_regions = ", ".join(sorted_regions)
    city_title = city.title()

    if not sorted_regions:
        example_one = f"{city_title}, State, Country"
        example_two = f"{city_title}, Country"
    elif len(sorted_regions) == 1:
        example_one = f"{city_title}, {sorted_regions[0]}"
        example_two = f"{city_title}, State, Country"
    else:
        example_one = f"{city_title}, {sorted_regions[0]}"
        example_two = f"{city_title}, {sorted_regions[1]}"

    return (
        f"The city '{city_title}' appears in multiple regions ({formatted_regions}). "
        "Please include city, state, and country for accurate details, "
        f"e.g., '{example_one}' or '{example_two}'."
    )


def get_city_ambiguity_description(city: str, fallback_regions: Optional[Iterable[str]] = None) -> Optional[str]:
    """Return human-readable ambiguity options for a city if known."""
    city_lower = (city or "").lower()

    if city_lower in KNOWN_AMBIGUOUS_LOCATIONS:
        return " or ".join(sorted(KNOWN_AMBIGUOUS_LOCATIONS[city_lower]))

    if fallback_regions:
        return " or ".join(sorted(set(fallback_regions)))

    return None
