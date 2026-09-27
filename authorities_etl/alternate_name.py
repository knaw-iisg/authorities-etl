"""Non-preferred ("see from", 4XX) and related ("see also", 5XX) heading
tracings -> ``sdo:alternateName``.

MARC authority format mirrors each 1XX heading tag with a 4XX/5XX
counterpart (100<->400/500, 110<->410/510, ... 155<->455/555). A 5XX
"related term" isn't strictly a synonym for the *same* concept the way a
4XX "used for" term is, but both get folded into ``sdo:alternateName`` here
-- schema.org has no distinct "related term" property, and the alternative
(dropping 5XX entirely) throws away real, if imprecise, information.
"""

from __future__ import annotations

ALTERNATE_NAME_TAGS = {
    "400", "410", "411", "430", "448", "450", "451", "455",
    "500", "510", "511", "530", "548", "550", "551", "555",
}
